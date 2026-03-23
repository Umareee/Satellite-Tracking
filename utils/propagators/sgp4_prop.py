"""SGP4 Propagator — Fast analytical orbit propagation using NORAD TLE data."""

import logging
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
from skyfield.api import Loader, EarthSatellite

from config import EARTH_RADIUS
from utils.propagators.base import BasePropagator

logger = logging.getLogger(__name__)

# Shared Skyfield resources (loaded once)
_loader = Loader('~/skyfield-data', expire=True)
_ts = _loader.timescale()


def get_timescale():
    """Get the shared timescale instance."""
    return _ts


class SGP4Propagator(BasePropagator):
    """
    SGP4/SDP4 analytical propagator via Skyfield.

    Uses the NORAD Simplified General Perturbations model.
    Suitable for general tracking with TLE data.
    Accuracy: ~1-10 km over 24 hours for LEO.
    """

    @property
    def name(self) -> str:
        return "SGP4"

    @property
    def description(self) -> str:
        return "NORAD analytical propagator (fast, TLE-based)"

    @property
    def accuracy_estimate(self) -> str:
        return "~1-10 km over 24h (LEO)"

    def _make_sat(self, tle: Tuple[str, str]) -> EarthSatellite:
        line1, line2 = tle
        return EarthSatellite(line1, line2, None, _ts)

    def get_position(self, satellite_tle: Tuple[str, str], observer) -> Optional[Dict[str, Any]]:
        try:
            sat = self._make_sat(satellite_tle)
            t = _ts.now()
            geocentric = sat.at(t)
            subpoint = geocentric.subpoint()

            difference = sat - observer
            topocentric = difference.at(t)
            alt, az, _ = topocentric.altaz()

            altitude = subpoint.elevation.km
            theta = np.arccos(EARTH_RADIUS / (EARTH_RADIUS + max(altitude, 0.1)))
            footprint_radius = np.degrees(theta)

            return {
                'lat': subpoint.latitude.degrees,
                'lon': subpoint.longitude.degrees,
                'alt': subpoint.elevation.km,
                'vel': np.linalg.norm(geocentric.velocity.km_per_s),
                'az': az.degrees,
                'el': alt.degrees,
                'time': t.utc_strftime('%Y-%m-%d %H:%M:%S UTC'),
                'footprint_radius': footprint_radius,
                'propagator': self.name,
            }
        except Exception as e:
            logger.error("SGP4 position calculation failed: %s", e)
            return None

    def calculate_trajectory(self, satellite_tle: Tuple[str, str],
                             points: int = 120, interval: int = 30) -> List[Tuple[float, float]]:
        try:
            sat = self._make_sat(satellite_tle)
            t = _ts.now()
            trajectory = []

            for seconds in range(0, points * interval, interval):
                future_t = _ts.tt_jd(t.tt + seconds / 86400.0)
                future_geo = sat.at(future_t)
                sp = future_geo.subpoint()
                lon = sp.longitude.degrees
                if lon > 180:
                    lon -= 360
                trajectory.append((lon, sp.latitude.degrees))

            return trajectory
        except Exception as e:
            logger.error("SGP4 trajectory calculation failed: %s", e)
            return []

    def calculate_passes(self, satellite_tle: Tuple[str, str], observer,
                         days: float = 7) -> List[Dict[str, Any]]:
        try:
            sat = self._make_sat(satellite_tle)
            t0 = _ts.now()
            t1 = _ts.tt_jd(t0.tt + days)

            times, events = sat.find_events(observer, t0, t1, altitude_degrees=0.0)

            passes = []
            i = 0
            while i < len(times):
                if events[i] == 0:  # Rise
                    rise_time = times[i]
                    difference = sat - observer
                    _, rise_az, _ = difference.at(rise_time).altaz()

                    i += 1
                    if i < len(times) and events[i] == 1:  # Culmination
                        culminate_time = times[i]
                        culm_alt, culm_az, _ = difference.at(culminate_time).altaz()

                        i += 1
                        if i < len(times) and events[i] == 2:  # Set
                            set_time = times[i]
                            _, set_az, _ = difference.at(set_time).altaz()

                            duration_s = (set_time.tt - rise_time.tt) * 86400
                            passes.append({
                                'rise_time': rise_time.utc_strftime('%Y-%m-%d %H:%M:%S'),
                                'rise_az': round(rise_az.degrees, 1),
                                'culminate_time': culminate_time.utc_strftime('%Y-%m-%d %H:%M:%S'),
                                'culm_alt': round(culm_alt.degrees, 1),
                                'culm_az': round(culm_az.degrees, 1),
                                'set_time': set_time.utc_strftime('%Y-%m-%d %H:%M:%S'),
                                'set_az': round(set_az.degrees, 1),
                                'duration': round(duration_s / 60, 1),
                            })
                        i += 1
                else:
                    i += 1

            logger.info("SGP4: Found %d passes over %.1f days", len(passes), days)
            return passes
        except Exception as e:
            logger.error("SGP4 pass calculation failed: %s", e)
            return []
