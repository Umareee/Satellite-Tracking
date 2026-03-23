# Constants and configuration
import logging

# Logging configuration
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_LEVEL = logging.INFO

# Theme definitions
THEMES = {
    'dark': {
        'bg': "#0a0e17",
        'bg_deeper': "#060a12",
        'card': "#111827",
        'card_hover': "#1a2332",
        'card_border': "#1e293b",
        'fg': "#e2e8f0",
        'fg_muted': "#94a3b8",
        'accent': "#06b6d4",
        'accent_hover': "#22d3ee",
        'green': "#10b981",
        'warning': "#f59e0b",
        'error': "#ef4444",
        'trajectory': "#06b6d4",
        'footprint': "#f97316",
        'border': "#334155",
        'map_coast': "#475569",
        'map_border': "#334155",
        'map_grid': "#475569",
        'map_face': "#0a0e17",
    },
    'light': {
        'bg': "#f1f5f9",
        'bg_deeper': "#e2e8f0",
        'card': "#ffffff",
        'card_hover': "#f8fafc",
        'card_border': "#cbd5e1",
        'fg': "#0f172a",
        'fg_muted': "#64748b",
        'accent': "#0891b2",
        'accent_hover': "#06b6d4",
        'green': "#059669",
        'warning': "#d97706",
        'error': "#dc2626",
        'trajectory': "#0891b2",
        'footprint': "#ea580c",
        'border': "#94a3b8",
        'map_coast': "#475569",
        'map_border': "#94a3b8",
        'map_grid': "#94a3b8",
        'map_face': "#f1f5f9",
    },
}

# Default theme
DEFAULT_THEME = 'dark'

# Quick access to current dark theme colors (used as defaults)
DARK_BG = THEMES['dark']['bg']
DARKER_BG = THEMES['dark']['bg_deeper']
CARD_BG = THEMES['dark']['card']
CARD_BG_HOVER = THEMES['dark']['card_hover']
CARD_BORDER = THEMES['dark']['card_border']
FG_COLOR = THEMES['dark']['fg']
FG_MUTED = THEMES['dark']['fg_muted']
ACCENT_COLOR = THEMES['dark']['accent']
ACCENT_HOVER = THEMES['dark']['accent_hover']
NEON_GREEN = THEMES['dark']['green']
WARNING_COLOR = THEMES['dark']['warning']
ERROR_COLOR = THEMES['dark']['error']
TRAJECTORY_COLOR = THEMES['dark']['trajectory']
GROUND_CIRCLE = THEMES['dark']['footprint']
BORDER_COLOR = THEMES['dark']['border']
HEADER_BG = "#0f172a"

# File paths
TLE_FILE = 'tle.txt'
PREFERENCES_FILE = 'preferences.json'

# Physics constants
EARTH_RADIUS = 6378.137  # km (WGS-84 equatorial radius)

# Update intervals
UPDATE_INTERVAL_MS = 500
TRAJECTORY_UPDATE_INTERVAL_S = 10
STALE_DATA_HOURS = 48

# Multi-tracking colors (up to 5 satellites)
MULTI_TRACK_COLORS = [
    "#06b6d4",  # cyan
    "#f97316",  # orange
    "#a855f7",  # purple
    "#10b981",  # green
    "#f43f5e",  # rose
]

# Pre-defined observer locations
LOCATIONS = {
    "Paris, France": (48.8566, 2.3522),
    "New York, USA": (40.7128, -74.0060),
    "Tokyo, Japan": (35.6762, 139.6503),
    "PIEAS, Islamabad": (33.6558, 73.2646),
    "London, UK": (51.5074, -0.1278),
    "Beijing, China": (39.9042, 116.4074),
    "Moscow, Russia": (55.7558, 37.6173),
    "Dubai, UAE": (25.2048, 55.2708),
    "Sydney, Australia": (-33.8688, 151.2093),
    "Los Angeles, USA": (34.0522, -118.2437),
    "Toronto, Canada": (43.651070, -79.347015),
    "Berlin, Germany": (52.5200, 13.4050),
    "Madrid, Spain": (40.4168, -3.7038),
    "Rome, Italy": (41.9028, 12.4964),
    "Seoul, South Korea": (37.5665, 126.9780),
    "Singapore": (1.3521, 103.8198),
    "Istanbul, Turkey": (41.0082, 28.9784),
    "Mumbai, India": (19.0760, 72.8777),
    "São Paulo, Brazil": (-23.5505, -46.6333),
    "Mexico City, Mexico": (19.4326, -99.1332),
    "Bangkok, Thailand": (13.7563, 100.5018),
    "Cairo, Egypt": (30.0444, 31.2357),
    "Johannesburg, South Africa": (-26.2041, 28.0473),
    "Buenos Aires, Argentina": (-34.6037, -58.3816),
    "Lagos, Nigeria": (6.5244, 3.3792),
    "Karachi, Pakistan": (24.8607, 67.0011),
    "Jakarta, Indonesia": (-6.2088, 106.8456),
    "Tehran, Iran": (35.6892, 51.3890),
    "Nairobi, Kenya": (-1.2921, 36.8219),
    "Riyadh, Saudi Arabia": (24.7136, 46.6753),
    "Kuala Lumpur, Malaysia": (3.1390, 101.6869),
    "Hanoi, Vietnam": (21.0278, 105.8342),
    "Baghdad, Iraq": (33.3128, 44.3615),
    "Manila, Philippines": (14.5995, 120.9842),
    "Lima, Peru": (-12.0464, -77.0428),
    "Athens, Greece": (37.9838, 23.7275),
    "Warsaw, Poland": (52.2297, 21.0122),
    "Brussels, Belgium": (50.8503, 4.3517),
    "Vienna, Austria": (48.2082, 16.3738),
    "Stockholm, Sweden": (59.3293, 18.0686),
    "Zurich, Switzerland": (47.3769, 8.5417),
    "Oslo, Norway": (59.9139, 10.7522),
    "Copenhagen, Denmark": (55.6761, 12.5683),
    "Helsinki, Finland": (60.1695, 24.9354),
    "Amsterdam, Netherlands": (52.3676, 4.9041),
    "Doha, Qatar": (25.276987, 51.520008),
    "Abu Dhabi, UAE": (24.4539, 54.3773),
    "Ankara, Turkey": (39.9334, 32.8597),
    "Santiago, Chile": (-33.4489, -70.6693),
    "Bucharest, Romania": (44.4268, 26.1025),
    "Islamabad, Pakistan": (33.6844, 73.0479),
    "San Francisco, USA": (37.7749, -122.4194),
    "Chicago, USA": (41.8781, -87.6298),
    "Houston, USA": (29.7604, -95.3698),
    "Boston, USA": (42.3601, -71.0589),
    "Philadelphia, USA": (39.9526, -75.1652),
    "Barcelona, Spain": (41.3851, 2.1734),
    "Munich, Germany": (48.1351, 11.5820),
    "Frankfurt, Germany": (50.1109, 8.6821),
    "Lisbon, Portugal": (38.7169, -9.1399),
    "Prague, Czech Republic": (50.0755, 14.4378),
    "Budapest, Hungary": (47.4979, 19.0402),
    "Belgrade, Serbia": (44.7866, 20.4489),
    "Sofia, Bulgaria": (42.6977, 23.3219),
    "Zagreb, Croatia": (45.8150, 15.9819),
    "Tallinn, Estonia": (59.4370, 24.7536),
    "Vilnius, Lithuania": (54.6872, 25.2797),
    "Riga, Latvia": (56.9496, 24.1052),
    "Tbilisi, Georgia": (41.7151, 44.8271),
    "Yerevan, Armenia": (40.1792, 44.4991),
    "Baku, Azerbaijan": (40.4093, 49.8671),
    "Almaty, Kazakhstan": (43.2220, 76.8512),
    "Tashkent, Uzbekistan": (41.2995, 69.2401),
    "Ulaanbaatar, Mongolia": (47.8864, 106.9057),
    "Colombo, Sri Lanka": (6.9271, 79.8612),
    "Kathmandu, Nepal": (27.7172, 85.3240),
    "Dhaka, Bangladesh": (23.8103, 90.4125),
    "Chennai, India": (13.0827, 80.2707),
    "Bangalore, India": (12.9716, 77.5946),
    "Hyderabad, India": (17.3850, 78.4867),
    "Pune, India": (18.5204, 73.8567),
    "Ahmedabad, India": (23.0225, 72.5714),
    "Cape Town, South Africa": (-33.9249, 18.4241),
    "Casablanca, Morocco": (33.5731, -7.5898),
    "Algiers, Algeria": (36.7538, 3.0588),
    "Addis Ababa, Ethiopia": (9.0300, 38.7400),
    "Accra, Ghana": (5.6037, -0.1870),
    "Kampala, Uganda": (0.3476, 32.5825),
    "Harare, Zimbabwe": (-17.8252, 31.0335),
    "Caracas, Venezuela": (10.4806, -66.9036),
    "Quito, Ecuador": (-0.1807, -78.4678),
    "Bogotá, Colombia": (4.7110, -74.0721),
    "La Paz, Bolivia": (-16.5000, -68.1500),
    "Montevideo, Uruguay": (-34.9011, -56.1645),
    "Asunción, Paraguay": (-25.2637, -57.5759),
    "Panama City, Panama": (8.9824, -79.5199),
    "San José, Costa Rica": (9.9281, -84.0907),
    "Port-au-Prince, Haiti": (18.5944, -72.3074),
    "Kingston, Jamaica": (18.0179, -76.8099),
    "Reykjavik, Iceland": (64.1355, -21.8954),
}

# Data sources
SATELLITE_CATEGORIES = {
    "ISS & Space Stations": "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
    "Starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
    "IntelSat": "https://celestrak.org/NORAD/elements/gp.php?GROUP=intelsat&FORMAT=tle",
    "GPS, Galileo, Beidou": "https://celestrak.org/NORAD/elements/gp.php?GROUP=gnss&FORMAT=tle",
    "Active Geosynchronous": "https://celestrak.org/NORAD/elements/gp.php?GROUP=geo&FORMAT=tle",
    "CubeSats": "https://celestrak.org/NORAD/elements/gp.php?GROUP=cubesat&FORMAT=tle",
    "Weather Satellites": "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
    "Amateur Radio": "https://celestrak.org/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle",
    "Science Satellites": "https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=tle",
    "Earth Observation": "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle",
}
