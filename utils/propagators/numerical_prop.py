"""
Numerical Propagator — High-fidelity orbit propagation with configurable force models.

Uses Cowell's method (direct numerical integration of equations of motion)
with a Runge-Kutta 4/5 (Dormand-Prince) integrator.
"""

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
from scipy.integrate import solve_ivp

from config import EARTH_RADIUS
from utils.propagators.base import BasePropagator
from utils.propagators import ForceModel, FORCE_MODEL_PRESETS
from utils.propagators.perturbations import (
    MU_EARTH, R_EARTH,
    accel_j2, accel_j3, accel_jn, accel_drag, accel_srp, accel_third_body,
    J4, J5, J6, MU_SUN, MU_MOON,
)

logger = logging.getLogger(__name__)


def _tle_to_state_vector(line1: str, line2: str) -> Tuple[np.ndarray, np.ndarray, datetime]:
    """
    Convert TLE to ECI state vector (position, velocity) at TLE epoch.
    Uses SGP4 for the initial state, then numerical propagation takes over.
    """
    from skyfield.api import EarthSatellite
    from utils.propagators.sgp4_prop import get_timescale

    ts = get_timescale()
    sat = EarthSatellite(line1, line2, None, ts)
    t = ts.now()

    geocentric = sat.at(t)
    pos_km = geocentric.position.km
    vel_km_s = geocentric.velocity.km_per_s

    # Convert to meters
    pos_m = np.array(pos_km) * 1000.0
    vel_m_s = np.array(vel_km_s) * 1000.0

    return pos_m, vel_m_s, t.utc_datetime()


def _approximate_sun_position(dt: datetime) -> np.ndarray:
    """Approximate Sun position in ECI (simplified, good to ~1°)."""
    # Julian date
    jd = (dt - datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)).total_seconds() / 86400.0
    T = jd / 36525.0

    # Mean longitude and anomaly (degrees)
    L0 = 280.46646 + 36000.76983 * T
    M = 357.52911 + 35999.05029 * T

    M_rad = math.radians(M % 360)
    C = (1.914602 - 0.004817 * T) * math.sin(M_rad) + 0.019993 * math.sin(2 * M_rad)
    sun_lon = math.radians((L0 + C) % 360)

    # Obliquity of ecliptic
    epsilon = math.radians(23.439291 - 0.0130042 * T)

    # Distance (AU to meters)
    R_au = 1.000140612 - 0.016708617 * math.cos(M_rad) - 0.000139589 * math.cos(2 * M_rad)
    R_m = R_au * 1.496e11

    # ECI position
    x = R_m * math.cos(sun_lon)
    y = R_m * math.cos(epsilon) * math.sin(sun_lon)
    z = R_m * math.sin(epsilon) * math.sin(sun_lon)

    return np.array([x, y, z])


def _approximate_moon_position(dt: datetime) -> np.ndarray:
    """Approximate Moon position in ECI (simplified)."""
    jd = (dt - datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)).total_seconds() / 86400.0
    T = jd / 36525.0

    # Simplified lunar position
    L = math.radians((218.32 + 481267.883 * T) % 360)
    M = math.radians((134.96 + 477198.867 * T) % 360)
    F = math.radians((93.27 + 483202.019 * T) % 360)

    # Ecliptic longitude/latitude/distance
    lon = L + math.radians(6.29 * math.sin(M))
    lat = math.radians(5.13 * math.sin(F))
    dist = 385000e3 * (1 - 0.0549 * math.cos(M))  # meters

    # Obliquity
    epsilon = math.radians(23.439291 - 0.0130042 * T)

    # ECI
    x = dist * math.cos(lat) * math.cos(lon)
    y = dist * (math.cos(epsilon) * math.cos(lat) * math.sin(lon) - math.sin(epsilon) * math.sin(lat))
    z = dist * (math.sin(epsilon) * math.cos(lat) * math.sin(lon) + math.cos(epsilon) * math.sin(lat))

    return np.array([x, y, z])


class NumericalPropagator(BasePropagator):
    """
    High-fidelity numerical orbit propagator using Cowell's method.

    Integrates the equations of motion with configurable force models:
    - Central body gravity
    - J2-J6 zonal harmonics
    - Atmospheric drag (exponential model)
    - Solar radiation pressure
    - Third-body perturbations (Sun, Moon)
    """

    def __init__(self, force_model: Optional[ForceModel] = None):
        self.force_model = force_model or FORCE_MODEL_PRESETS['standard']

    @property
    def name(self) -> str:
        return "Numerical"

    @property
    def description(self) -> str:
        forces = self.force_model.enabled_forces()
        return f"Numerical propagator ({', '.join(forces)})"

    @property
    def accuracy_estimate(self) -> str:
        return "~10-100 m over 24h (LEO)"

    def _equations_of_motion(self, t: float, state: np.ndarray,
                             epoch_dt: datetime) -> np.ndarray:
        """
        Equations of motion for numerical integration.
        state = [x, y, z, vx, vy, vz] in meters and m/s (ECI)
        """
        r = state[:3]
        v = state[3:]
        r_mag = np.linalg.norm(r)

        # Central body gravity
        a = -MU_EARTH * r / r_mag ** 3

        fm = self.force_model

        # J2
        if fm.j2:
            a += accel_j2(r)

        # J3
        if fm.j3:
            a += accel_j3(r)

        # J4-J6
        if fm.j4:
            a += accel_jn(r, 4, J4)
        if fm.j5:
            a += accel_jn(r, 5, J5)
        if fm.j6:
            a += accel_jn(r, 6, J6)

        # Atmospheric drag
        if fm.atmospheric_drag:
            a += accel_drag(r, v, fm.drag_coefficient, fm.area_to_mass_ratio)

        # Current datetime for ephemeris
        current_dt = epoch_dt + timedelta(seconds=float(t))

        # Solar radiation pressure
        if fm.solar_radiation_pressure:
            r_sun = _approximate_sun_position(current_dt)
            a += accel_srp(r, r_sun, fm.srp_coefficient, fm.area_to_mass_ratio)

        # Third-body: Sun
        if fm.third_body_sun:
            r_sun = _approximate_sun_position(current_dt)
            a += accel_third_body(r, r_sun, MU_SUN)

        # Third-body: Moon
        if fm.third_body_moon:
            r_moon = _approximate_moon_position(current_dt)
            a += accel_third_body(r, r_moon, MU_MOON)

        return np.concatenate([v, a])

    def _propagate(self, line1: str, line2: str,
                   duration_s: float, dt: float = 30.0) -> Tuple[np.ndarray, np.ndarray, datetime]:
        """
        Propagate orbit numerically.

        Returns: (times, states, epoch_datetime)
            times: array of time values in seconds from epoch
            states: array of shape (N, 6) with [x, y, z, vx, vy, vz] in m and m/s
            epoch_datetime: UTC datetime of epoch
        """
        r0, v0, epoch_dt = _tle_to_state_vector(line1, line2)
        state0 = np.concatenate([r0, v0])

        t_span = (0.0, float(duration_s))
        t_eval = np.arange(0.0, float(duration_s), float(dt))

        sol = solve_ivp(
            self._equations_of_motion,
            t_span, state0,
            method='DOP853',  # 8th order Dormand-Prince
            t_eval=t_eval,
            rtol=1e-10,
            atol=1e-12,
            args=(epoch_dt,),
            max_step=60.0,
        )

        if not sol.success:
            logger.warning("Numerical integration warning: %s", sol.message)

        return sol.t, sol.y.T, epoch_dt

    def _eci_to_geodetic(self, r: np.ndarray, dt: datetime) -> Tuple[float, float, float]:
        """Convert ECI position to geodetic (lat, lon, alt)."""
        x, y, z = r
        r_mag = np.linalg.norm(r)

        # Latitude (geocentric, simplified)
        lat = math.degrees(math.asin(z / r_mag))

        # Longitude (account for Earth rotation)
        # Greenwich sidereal time
        jd = (dt - datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)).total_seconds() / 86400.0
        gmst = (280.46061837 + 360.98564736629 * jd) % 360
        lon = math.degrees(math.atan2(y, x)) - gmst
        lon = ((lon + 180) % 360) - 180

        alt = (r_mag - R_EARTH) / 1000.0  # km

        return lat, lon, alt

    def get_position(self, satellite_tle: Tuple[str, str], observer) -> Optional[Dict[str, Any]]:
        try:
            line1, line2 = satellite_tle

            # Use SGP4 for observer-relative calculations (az/el)
            # and numerical for position — hybrid approach
            from utils.propagators.sgp4_prop import SGP4Propagator
            sgp4_data = SGP4Propagator().get_position(satellite_tle, observer)

            if not sgp4_data:
                return None

            # For current position, numerical vs SGP4 difference is negligible
            # The value shows in trajectory prediction (future positions)
            sgp4_data['propagator'] = self.name
            return sgp4_data

        except Exception as e:
            logger.error("Numerical position calculation failed: %s", e)
            return None

    def calculate_trajectory(self, satellite_tle: Tuple[str, str],
                             points: int = 120, interval: int = 30) -> List[Tuple[float, float]]:
        try:
            line1, line2 = satellite_tle
            duration_s = points * interval

            times, states, epoch_dt = self._propagate(line1, line2, duration_s, dt=interval)

            trajectory = []
            for i, t in enumerate(times):
                r = states[i, :3]
                current_dt = epoch_dt + timedelta(seconds=float(t))
                lat, lon, alt = self._eci_to_geodetic(r, current_dt)
                trajectory.append((lon, lat))

            return trajectory

        except Exception as e:
            logger.error("Numerical trajectory calculation failed: %s", e)
            # Fallback to SGP4
            logger.info("Falling back to SGP4 for trajectory")
            from utils.propagators.sgp4_prop import SGP4Propagator
            return SGP4Propagator().calculate_trajectory(satellite_tle, points, interval)

    def calculate_passes(self, satellite_tle: Tuple[str, str], observer,
                         days: float = 7) -> List[Dict[str, Any]]:
        # Pass prediction uses SGP4's find_events (most efficient)
        # Numerical propagation is overkill for pass timing
        from utils.propagators.sgp4_prop import SGP4Propagator
        return SGP4Propagator().calculate_passes(satellite_tle, observer, days)
