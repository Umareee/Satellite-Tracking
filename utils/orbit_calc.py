import numpy as np
from skyfield.api import Loader, EarthSatellite
from config import EARTH_RADIUS

load = Loader('~/skyfield-data', expire=True)
ts = load.timescale()


def get_satellite_position(satellite_tle, observer):
    """Calculate current satellite position"""
    line1, line2 = satellite_tle
    sat = EarthSatellite(line1, line2, None, ts)
    t = ts.now()
    geocentric = sat.at(t)
    subpoint = geocentric.subpoint()
    difference = sat - observer
    topocentric = difference.at(t)
    alt, az, _ = topocentric.altaz()

    altitude = subpoint.elevation.km
    h = altitude
    theta = np.arccos(EARTH_RADIUS / (EARTH_RADIUS + h))
    footprint_radius = np.degrees(theta)

    return {
        'lat': subpoint.latitude.degrees,
        'lon': subpoint.longitude.degrees,
        'alt': subpoint.elevation.km,
        'vel': np.linalg.norm(geocentric.velocity.km_per_s),
        'az': az.degrees,
        'el': alt.degrees,
        'time': t.utc_strftime('%Y-%m-%d %H:%M:%S UTC'),
        'footprint_radius': footprint_radius
    }


def calculate_trajectory(satellite_tle, points=120, interval=30):
    """Calculate satellite trajectory"""
    line1, line2 = satellite_tle
    sat = EarthSatellite(line1, line2, None, ts)
    t = ts.now()
    trajectory = []

    for seconds in range(0, points * interval, interval):
        future_t = ts.tt_jd(t.tt + seconds / 86400.0)
        future_geocentric = sat.at(future_t)
        future_subpoint = future_geocentric.subpoint()
        lon = future_subpoint.longitude.degrees
        if lon > 180:
            lon -= 360
        trajectory.append((lon, future_subpoint.latitude.degrees))

    return trajectory


def calculate_passes(satellite_tle, observer, days=7):
    """Calculate satellite passes over observer location"""
    line1, line2 = satellite_tle
    satellite = EarthSatellite(line1, line2, None, ts)

    t0 = ts.now()
    t1 = ts.tt_jd(t0.tt + days)

    times, events = satellite.find_events(observer, t0, t1, altitude_degrees=0.0)

    passes = []
    i = 0
    while i < len(times):
        if events[i] == 0:  # Rise event
            rise_time = times[i]
            difference = satellite - observer
            rise_topocentric = difference.at(rise_time)
            _, rise_az, _ = rise_topocentric.altaz()

            i += 1
            if i < len(times) and events[i] == 1:  # Culmination event
                culminate_time = times[i]
                culminate_topocentric = difference.at(culminate_time)
                _, culm_az, _ = culminate_topocentric.altaz()

                i += 1
                if i < len(times) and events[i] == 2:  # Set event
                    set_time = times[i]
                    set_topocentric = difference.at(set_time)
                    _, set_az, _ = set_topocentric.altaz()

                    duration_seconds = (set_time.tt - rise_time.tt) * 86400
                    duration_minutes = round(duration_seconds / 60, 1)

                    passes.append({
                        'rise_time': rise_time.utc_strftime('%Y-%m-%d %H:%M:%S'),
                        'rise_az': round(rise_az.degrees, 1),
                        'culminate_time': culminate_time.utc_strftime('%Y-%m-%d %H:%M:%S'),
                        'culm_az': round(culm_az.degrees, 1),
                        'set_time': set_time.utc_strftime('%Y-%m-%d %H:%M:%S'),
                        'set_az': round(set_az.degrees, 1),
                        'duration': duration_minutes
                    })
                i += 1
        else:
            i += 1

    return passes