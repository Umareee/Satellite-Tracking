import requests
import os
from skyfield.api import Loader, EarthSatellite
from config import TLE_FILE
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

load = Loader('~/skyfield-data', expire=True)
ts = load.timescale()


def parse_tle(tle_text):
    """Parse TLE data into satellite dictionary"""
    satellites = {}
    lines = [line.strip() for line in tle_text.splitlines() if line.strip()]
    for i in range(0, len(lines) - 2, 3):
        name, line1, line2 = lines[i:i + 3]
        satellites[name] = (line1, line2)
    return satellites


def fetch_tle_data(url):
    """Fetch TLE data from URL"""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    tle_text = response.text.strip()
    if not tle_text:
        raise ValueError("Received empty TLE data")
    return tle_text


def save_tle_data(tle_text):
    """Save TLE data to file"""
    tle_file_path = resource_path(TLE_FILE)
    with open(tle_file_path, 'w') as f:
        f.write(tle_text)
    return parse_tle(tle_text)


def load_tle_data():
    """Load TLE data from file"""
    tle_file_path = resource_path(TLE_FILE)
    if not os.path.exists(tle_file_path):
        return {}

    with open(tle_file_path, 'r') as f:
        tle_text = f.read()

    return parse_tle(tle_text)