"""
Data manager — handles TLE data lifecycle (load, fetch, save, cache).
Separated from UI concerns.
"""

import logging
import threading
from typing import Dict, Tuple, Optional, Callable

from utils.satellite_data import (load_tle_data, fetch_tle_data, save_tle_data,
                                  get_tle_age_hours)

logger = logging.getLogger(__name__)


class DataManager:
    """Manages satellite TLE data loading, fetching, and caching."""

    def __init__(self):
        self.satellites: Dict[str, Tuple[str, str]] = {}
        self._fetching = False

    @property
    def is_fetching(self) -> bool:
        return self._fetching

    @property
    def satellite_count(self) -> int:
        return len(self.satellites)

    @property
    def data_age_hours(self) -> Optional[float]:
        return get_tle_age_hours()

    def load_local(self) -> bool:
        """Load TLE data from local file. Returns True if data loaded."""
        self.satellites = load_tle_data()
        count = len(self.satellites)
        if count > 0:
            logger.info("Loaded %d satellites from local file", count)
        return count > 0

    def fetch_remote(self, url: str,
                     on_success: Optional[Callable] = None,
                     on_error: Optional[Callable[[str], None]] = None):
        """
        Fetch TLE data from remote URL in a background thread.

        Args:
            url: Celestrak URL to fetch from
            on_success: Callback (no args) when fetch completes
            on_error: Callback (error_message) when fetch fails
        """
        if self._fetching:
            logger.warning("Fetch already in progress, ignoring request")
            return

        self._fetching = True

        def _do_fetch():
            try:
                tle_text = fetch_tle_data(url)
                self.satellites = save_tle_data(tle_text)

                if not self.satellites:
                    raise ValueError("Fetched data contained no valid satellites")

                logger.info("TLE data updated: %d satellites", len(self.satellites))
                if on_success:
                    on_success()
            except (ConnectionError, TimeoutError, RuntimeError, ValueError) as e:
                logger.error("TLE fetch failed: %s", e)
                if on_error:
                    on_error(str(e))
            finally:
                self._fetching = False

        threading.Thread(target=_do_fetch, daemon=True).start()

    def has_satellite(self, name: str) -> bool:
        return name in self.satellites

    def get_tle(self, name: str) -> Optional[Tuple[str, str]]:
        return self.satellites.get(name)

    def satellite_names(self):
        return list(self.satellites.keys())
