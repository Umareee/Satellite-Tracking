import logging
import os
import re
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional

import requests

from config import TLE_FILE
from utils.resource_utils import resource_path

logger = logging.getLogger(__name__)

# TLE line validation patterns
TLE_LINE1_PATTERN = re.compile(r'^1 ')
TLE_LINE2_PATTERN = re.compile(r'^2 ')


def validate_tle_lines(name: str, line1: str, line2: str) -> bool:
    """Validate that TLE lines have correct format."""
    if not TLE_LINE1_PATTERN.match(line1):
        logger.warning("Invalid TLE line 1 for '%s': %s", name, line1[:20])
        return False
    if not TLE_LINE2_PATTERN.match(line2):
        logger.warning("Invalid TLE line 2 for '%s': %s", name, line2[:20])
        return False
    if len(line1) < 69 or len(line2) < 69:
        logger.warning("TLE lines too short for '%s'", name)
        return False
    return True


def parse_tle(tle_text: str) -> Dict[str, Tuple[str, str]]:
    """Parse TLE data into satellite dictionary with validation."""
    satellites = {}
    lines = [line.strip() for line in tle_text.splitlines() if line.strip()]

    if len(lines) < 3:
        logger.warning("TLE data too short: %d lines", len(lines))
        return satellites

    skipped = 0
    for i in range(0, len(lines) - 2, 3):
        name = lines[i]
        line1 = lines[i + 1]
        line2 = lines[i + 2]

        if validate_tle_lines(name, line1, line2):
            satellites[name] = (line1, line2)
        else:
            skipped += 1

    if skipped:
        logger.warning("Skipped %d invalid TLE entries", skipped)

    logger.info("Parsed %d satellites from TLE data", len(satellites))
    return satellites


def fetch_tle_data(url: str) -> str:
    """Fetch TLE data from URL."""
    logger.info("Fetching TLE data from %s", url)
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.ConnectionError:
        raise ConnectionError("No internet connection. Please check your network.")
    except requests.Timeout:
        raise TimeoutError("Request timed out. The server may be busy.")
    except requests.HTTPError as e:
        raise RuntimeError(f"Server returned error: {e.response.status_code}")

    tle_text = response.text.strip()
    if not tle_text:
        raise ValueError("Received empty TLE data from server")

    logger.info("Fetched %d bytes of TLE data", len(tle_text))
    return tle_text


def save_tle_data(tle_text: str) -> Dict[str, Tuple[str, str]]:
    """Save TLE data to file and return parsed satellites."""
    tle_file_path = resource_path(TLE_FILE)

    # Backup existing file before overwriting
    if os.path.exists(tle_file_path):
        backup_path = tle_file_path + '.bak'
        try:
            os.replace(tle_file_path, backup_path)
            logger.info("Backed up existing TLE file to %s", backup_path)
        except OSError as e:
            logger.warning("Could not create backup: %s", e)

    with open(tle_file_path, 'w') as f:
        f.write(tle_text)

    logger.info("Saved TLE data to %s", tle_file_path)
    return parse_tle(tle_text)


def load_tle_data() -> Dict[str, Tuple[str, str]]:
    """Load TLE data from file."""
    tle_file_path = resource_path(TLE_FILE)
    if not os.path.exists(tle_file_path):
        logger.info("No TLE file found at %s", tle_file_path)
        return {}

    with open(tle_file_path, 'r') as f:
        tle_text = f.read()

    if not tle_text.strip():
        logger.warning("TLE file is empty")
        return {}

    return parse_tle(tle_text)


def get_tle_age_hours() -> Optional[float]:
    """Get the age of the TLE file in hours. Returns None if file doesn't exist."""
    tle_file_path = resource_path(TLE_FILE)
    if not os.path.exists(tle_file_path):
        return None

    mtime = os.path.getmtime(tle_file_path)
    mtime_utc = datetime.utcfromtimestamp(mtime).replace(tzinfo=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - mtime_utc).total_seconds()
    return max(age_seconds / 3600, 0.0)
