"""Abstract base class for all propagators."""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any


class BasePropagator(ABC):
    """Base class that all propagators must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the propagator."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of the propagator capabilities."""
        ...

    @property
    @abstractmethod
    def accuracy_estimate(self) -> str:
        """Estimated accuracy (e.g., '1-10 km over 24h')."""
        ...

    @abstractmethod
    def get_position(self, satellite_tle: Tuple[str, str], observer) -> Optional[Dict[str, Any]]:
        """
        Calculate current satellite position.

        Returns dict with keys:
            lat, lon, alt, vel, az, el, time, footprint_radius
            + any propagator-specific extras
        """
        ...

    @abstractmethod
    def calculate_trajectory(
        self, satellite_tle: Tuple[str, str],
        points: int = 120, interval: int = 30,
    ) -> List[Tuple[float, float]]:
        """
        Calculate future trajectory as list of (lon, lat) tuples.

        Args:
            points: Number of trajectory points
            interval: Seconds between each point
        """
        ...

    @abstractmethod
    def calculate_passes(
        self, satellite_tle: Tuple[str, str], observer,
        days: float = 7,
    ) -> List[Dict[str, Any]]:
        """
        Calculate visible passes over observer location.

        Returns list of dicts with keys:
            rise_time, rise_az, culminate_time, culm_alt, culm_az,
            set_time, set_az, duration
        """
        ...

    def get_orbital_elements(self, satellite_tle: Tuple[str, str]) -> Optional[Dict[str, Any]]:
        """
        Extract orbital elements from TLE.
        Default implementation parses TLE directly.
        """
        try:
            line1, line2 = satellite_tle

            # Parse TLE line 2 for orbital elements
            inclination = float(line2[8:16].strip())
            raan = float(line2[17:25].strip())
            eccentricity = float(f"0.{line2[26:33].strip()}")
            arg_perigee = float(line2[34:42].strip())
            mean_anomaly = float(line2[43:51].strip())
            mean_motion = float(line2[52:63].strip())
            rev_number = int(line2[63:68].strip())

            # Parse line 1 for metadata
            norad_id = line1[2:7].strip()
            classification = line1[7]
            epoch_year = int(line1[18:20])
            epoch_day = float(line1[20:32])
            bstar = self._parse_bstar(line1[53:61])

            # Derived values
            period_minutes = 1440.0 / mean_motion if mean_motion > 0 else 0
            semi_major_axis = (398600.4418 * (period_minutes * 60 / (2 * 3.14159265)) ** 2) ** (1/3) if period_minutes > 0 else 0
            apogee_km = semi_major_axis * (1 + eccentricity) - 6371 if semi_major_axis > 0 else 0
            perigee_km = semi_major_axis * (1 - eccentricity) - 6371 if semi_major_axis > 0 else 0

            return {
                'norad_id': norad_id,
                'classification': classification,
                'epoch_year': 2000 + epoch_year if epoch_year < 57 else 1900 + epoch_year,
                'epoch_day': epoch_day,
                'bstar': bstar,
                'inclination': inclination,
                'raan': raan,
                'eccentricity': eccentricity,
                'arg_perigee': arg_perigee,
                'mean_anomaly': mean_anomaly,
                'mean_motion': mean_motion,
                'rev_number': rev_number,
                'period_minutes': round(period_minutes, 2),
                'semi_major_axis_km': round(semi_major_axis, 2),
                'apogee_km': round(apogee_km, 2),
                'perigee_km': round(perigee_km, 2),
            }
        except (ValueError, IndexError) as e:
            return None

    @staticmethod
    def _parse_bstar(bstar_str: str) -> float:
        """Parse B* drag term from TLE format (e.g., ' 12345-4')."""
        try:
            s = bstar_str.strip()
            if not s or s == '00000-0':
                return 0.0
            # Format: mantissa + sign + exponent  e.g., "12345-4"
            if '-' in s[1:] or '+' in s[1:]:
                for i in range(1, len(s)):
                    if s[i] in ('+', '-'):
                        mantissa = float(f"0.{s[:i].strip()}")
                        exponent = int(s[i:])
                        return mantissa * 10 ** exponent
            return float(s)
        except (ValueError, IndexError):
            return 0.0
