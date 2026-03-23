"""
Tracking controller — manages satellite tracking state and computation.
Separated from UI and data concerns.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any

from utils.orbit_calc import get_satellite_position, calculate_trajectory
from config import TRAJECTORY_UPDATE_INTERVAL_S, MULTI_TRACK_COLORS

logger = logging.getLogger(__name__)


class TrackingController:
    """Manages satellite tracking state, trajectories, and multi-track."""

    def __init__(self):
        self.current_sat: Optional[str] = None
        self.is_playing = False

        # Primary trajectory cache
        self._trajectory: List[Tuple[float, float]] = []
        self._trajectory_updated: Optional[datetime] = None

        # Multi-track state
        self.tracked_sats: List[str] = []
        self._tracked_trajectories: Dict[str, List[Tuple[float, float]]] = {}
        self._tracked_last_update: Dict[str, datetime] = {}

    def select_satellite(self, name: str):
        """Select a satellite as the primary tracked object."""
        self.current_sat = name
        self._trajectory_updated = None  # Force trajectory recalculation
        logger.info("Selected satellite: %s", name)

    def toggle_play(self) -> bool:
        """Toggle play/pause. Returns new is_playing state."""
        self.is_playing = not self.is_playing
        if self.is_playing:
            logger.info("Started tracking: %s", self.current_sat)
        return self.is_playing

    def stop(self):
        """Stop tracking."""
        self.is_playing = False

    def set_tracked_list(self, names: List[str]):
        """Update the multi-track satellite list."""
        self.tracked_sats = names
        # Clean stale caches
        for key in list(self._tracked_trajectories.keys()):
            if key not in names:
                del self._tracked_trajectories[key]
                self._tracked_last_update.pop(key, None)

    def compute_update(self, satellites: dict, observer) -> Optional[Dict[str, Any]]:
        """
        Compute a full tracking update.

        Returns dict with:
            'data': primary satellite position data
            'trajectory': primary trajectory
            'multi': list of multi-tracked satellite data
        Or None if no satellite selected.
        """
        if not self.current_sat or self.current_sat not in satellites:
            return None

        now = datetime.now(timezone.utc)

        # Primary trajectory (cached, refreshed periodically)
        if (self._trajectory_updated is None or
                (now - self._trajectory_updated).total_seconds() > TRAJECTORY_UPDATE_INTERVAL_S):
            self._trajectory = calculate_trajectory(satellites[self.current_sat])
            self._trajectory_updated = now

        # Primary position
        data = get_satellite_position(satellites[self.current_sat], observer)
        if not data:
            return None
        data['name'] = self.current_sat

        # Multi-tracked satellites
        multi_data: List[Dict[str, Any]] = []
        for i, sat_name in enumerate(self.tracked_sats):
            if sat_name not in satellites or sat_name == self.current_sat:
                continue

            # Trajectory cache
            last = self._tracked_last_update.get(sat_name)
            if last is None or (now - last).total_seconds() > TRAJECTORY_UPDATE_INTERVAL_S:
                self._tracked_trajectories[sat_name] = calculate_trajectory(satellites[sat_name])
                self._tracked_last_update[sat_name] = now

            sat_data = get_satellite_position(satellites[sat_name], observer)
            if sat_data:
                sat_data['name'] = sat_name
                sat_data['color'] = MULTI_TRACK_COLORS[i % len(MULTI_TRACK_COLORS)]
                sat_data['trajectory'] = self._tracked_trajectories.get(sat_name, [])
                multi_data.append(sat_data)

        return {
            'data': data,
            'trajectory': self._trajectory,
            'multi': multi_data,
        }
