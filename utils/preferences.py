"""
User preferences persistence — save/load settings to JSON file.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

from config import PREFERENCES_FILE
from utils.resource_utils import resource_path

logger = logging.getLogger(__name__)

_DEFAULTS = {
    'theme': 'dark',
    'observer_lat': 40.7128,
    'observer_lon': -74.0060,
    'observer_name': 'New York, USA (40.7128 N, 74.0060 W)',
    'last_satellite': None,
    'last_category': 'ISS & Space Stations',
}


def _get_path() -> str:
    return resource_path(PREFERENCES_FILE)


def load_preferences() -> Dict[str, Any]:
    """Load user preferences from disk. Returns defaults if file missing."""
    path = _get_path()
    if not os.path.exists(path):
        logger.info("No preferences file, using defaults")
        return _DEFAULTS.copy()

    try:
        with open(path, 'r') as f:
            saved = json.load(f)
        # Merge with defaults (in case new keys added in updates)
        prefs = _DEFAULTS.copy()
        prefs.update(saved)
        logger.info("Loaded preferences from %s", path)
        return prefs
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load preferences: %s", e)
        return _DEFAULTS.copy()


def save_preferences(prefs: Dict[str, Any]):
    """Save user preferences to disk."""
    path = _get_path()
    try:
        with open(path, 'w') as f:
            json.dump(prefs, f, indent=2)
        logger.info("Saved preferences to %s", path)
    except OSError as e:
        logger.error("Failed to save preferences: %s", e)


def get_pref(key: str, default: Any = None) -> Any:
    """Get a single preference value."""
    prefs = load_preferences()
    return prefs.get(key, default)


def set_pref(key: str, value: Any):
    """Set a single preference value and save."""
    prefs = load_preferences()
    prefs[key] = value
    save_preferences(prefs)
