"""
Perturbation force models for numerical orbit propagation.

Implements acceleration functions for:
    - Earth gravity harmonics (J2 through J6)
    - Atmospheric drag (exponential density model)
    - Solar radiation pressure
    - Third-body perturbations (Sun, Moon)
"""

import logging
import math
from typing import Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ============================================================
# Constants
# ============================================================
MU_EARTH = 3.986004418e14       # Earth gravitational parameter (m³/s²)
R_EARTH = 6.3781e6              # Earth equatorial radius (m)
OMEGA_EARTH = 7.2921159e-5      # Earth rotation rate (rad/s)

# Zonal harmonics (unnormalized)
J2 = 1.08263e-3
J3 = -2.53266e-6
J4 = -1.61962e-6
J5 = -2.27289e-7
J6 = 5.40681e-7

# Solar radiation pressure
P_SUN = 4.56e-6                 # Solar radiation pressure at 1 AU (N/m²)
AU = 1.496e11                   # 1 AU in meters

# Third body parameters
MU_SUN = 1.32712440018e20       # Sun gravitational parameter (m³/s²)
MU_MOON = 4.9048695e12          # Moon gravitational parameter (m³/s²)

# Atmospheric density model (exponential, simplified)
# Format: (base_altitude_km, base_density_kg_m3, scale_height_km)
ATMOSPHERE_LAYERS = [
    (0, 1.225, 7.249),
    (25, 3.899e-2, 6.349),
    (30, 1.774e-2, 6.682),
    (40, 3.972e-3, 7.554),
    (50, 1.057e-3, 8.382),
    (60, 3.206e-4, 7.714),
    (70, 8.770e-5, 6.549),
    (80, 1.905e-5, 5.799),
    (90, 3.396e-6, 5.382),
    (100, 5.297e-7, 5.877),
    (110, 9.661e-8, 7.263),
    (120, 2.438e-8, 9.473),
    (130, 8.484e-9, 12.636),
    (140, 3.845e-9, 16.149),
    (150, 2.070e-9, 22.523),
    (180, 5.464e-10, 29.740),
    (200, 2.789e-10, 37.105),
    (250, 7.248e-11, 45.546),
    (300, 2.418e-11, 53.628),
    (350, 9.518e-12, 53.298),
    (400, 3.725e-12, 58.515),
    (450, 1.585e-12, 60.828),
    (500, 6.967e-13, 63.822),
    (600, 1.454e-13, 71.835),
    (700, 3.614e-14, 88.667),
    (800, 1.170e-14, 124.64),
    (900, 5.245e-15, 181.05),
    (1000, 3.019e-15, 268.00),
]


# ============================================================
# Acceleration functions
# ============================================================

def accel_j2(r: np.ndarray) -> np.ndarray:
    """J2 oblateness perturbation acceleration."""
    x, y, z = r
    r_mag = np.linalg.norm(r)
    r2 = r_mag ** 2
    z2_r2 = (z / r_mag) ** 2
    factor = -1.5 * J2 * MU_EARTH * R_EARTH ** 2 / r_mag ** 5

    ax = factor * x * (1 - 5 * z2_r2)
    ay = factor * y * (1 - 5 * z2_r2)
    az = factor * z * (3 - 5 * z2_r2)
    return np.array([ax, ay, az])


def accel_j3(r: np.ndarray) -> np.ndarray:
    """J3 perturbation acceleration."""
    x, y, z = r
    r_mag = np.linalg.norm(r)
    z_r = z / r_mag
    factor = -0.5 * J3 * MU_EARTH * R_EARTH ** 3 / r_mag ** 6

    ax = factor * 5 * x * (7 * z_r ** 3 - 3 * z_r)
    ay = factor * 5 * y * (7 * z_r ** 3 - 3 * z_r)
    az = factor * (3 - 30 * z_r ** 2 + 35 * z_r ** 4) * r_mag
    return np.array([ax, ay, az])


def accel_jn(r: np.ndarray, n: int, jn_val: float) -> np.ndarray:
    """Generic Jn zonal harmonic perturbation (simplified for J4-J6)."""
    x, y, z = r
    r_mag = np.linalg.norm(r)
    # Simplified: scale J2 pattern with higher-order coefficient
    z_r = z / r_mag
    factor = -(n + 1) / 2.0 * jn_val * MU_EARTH * R_EARTH ** n / r_mag ** (n + 2)

    ax = factor * x * (1 - (2 * n + 1) * z_r ** 2)
    ay = factor * y * (1 - (2 * n + 1) * z_r ** 2)
    az = factor * z * ((2 * n - 1) - (2 * n + 1) * z_r ** 2)
    return np.array([ax, ay, az])


def atmospheric_density(altitude_km: float) -> float:
    """
    Exponential atmospheric density model.
    Returns density in kg/m³ for given altitude in km.
    """
    if altitude_km < 0:
        return ATMOSPHERE_LAYERS[0][1]
    if altitude_km > 1000:
        return 0.0

    # Find the appropriate layer
    layer = ATMOSPHERE_LAYERS[0]
    for base_alt, base_rho, scale_h in ATMOSPHERE_LAYERS:
        if altitude_km >= base_alt:
            layer = (base_alt, base_rho, scale_h)
        else:
            break

    base_alt, base_rho, scale_h = layer
    return base_rho * math.exp(-(altitude_km - base_alt) / scale_h)


def accel_drag(r: np.ndarray, v: np.ndarray,
               cd: float = 2.2, area_to_mass: float = 0.01) -> np.ndarray:
    """
    Atmospheric drag acceleration.

    Args:
        r: Position vector (m) in ECI
        v: Velocity vector (m/s) in ECI
        cd: Drag coefficient (typically 2.0-2.5)
        area_to_mass: Cross-sectional area / mass ratio (m²/kg)
    """
    r_mag = np.linalg.norm(r)
    alt_km = (r_mag - R_EARTH) / 1000.0

    if alt_km > 1000 or alt_km < 0:
        return np.zeros(3)

    rho = atmospheric_density(alt_km)
    if rho == 0:
        return np.zeros(3)

    # Velocity relative to rotating atmosphere
    omega_vec = np.array([0, 0, OMEGA_EARTH])
    v_rel = v - np.cross(omega_vec, r)
    v_rel_mag = np.linalg.norm(v_rel)

    if v_rel_mag == 0:
        return np.zeros(3)

    # Drag acceleration: a = -0.5 * Cd * (A/m) * rho * |v_rel| * v_rel
    return -0.5 * cd * area_to_mass * rho * v_rel_mag * v_rel


def accel_srp(r: np.ndarray, r_sun: np.ndarray,
              cr: float = 1.8, area_to_mass: float = 0.01) -> np.ndarray:
    """
    Solar radiation pressure acceleration.

    Args:
        r: Satellite position (m) in ECI
        r_sun: Sun position (m) in ECI
        cr: SRP coefficient (1.0 = perfect absorber, 2.0 = perfect reflector)
        area_to_mass: Area/mass ratio (m²/kg)
    """
    r_sat_sun = r_sun - r
    dist = np.linalg.norm(r_sat_sun)

    if dist == 0:
        return np.zeros(3)

    # Check if satellite is in Earth's shadow (cylindrical model)
    if _in_shadow(r, r_sun):
        return np.zeros(3)

    # SRP acceleration
    return -cr * P_SUN * area_to_mass * AU ** 2 / dist ** 2 * (r_sat_sun / dist)


def accel_third_body(r: np.ndarray, r_body: np.ndarray, mu_body: float) -> np.ndarray:
    """
    Third-body gravitational perturbation.

    Args:
        r: Satellite position (m) in ECI
        r_body: Third body position (m) in ECI
        mu_body: Third body gravitational parameter (m³/s²)
    """
    r_sat_body = r_body - r
    dist_sat_body = np.linalg.norm(r_sat_body)
    dist_body = np.linalg.norm(r_body)

    if dist_sat_body == 0 or dist_body == 0:
        return np.zeros(3)

    return mu_body * (r_sat_body / dist_sat_body ** 3 - r_body / dist_body ** 3)


def _in_shadow(r_sat: np.ndarray, r_sun: np.ndarray) -> bool:
    """Check if satellite is in Earth's shadow (cylindrical model)."""
    r_sun_norm = r_sun / np.linalg.norm(r_sun)
    projection = np.dot(r_sat, r_sun_norm)

    if projection > 0:
        # Satellite is on the sun side
        return False

    # Distance from satellite to Sun-Earth line
    perpendicular = r_sat - projection * r_sun_norm
    perp_dist = np.linalg.norm(perpendicular)

    return perp_dist < R_EARTH
