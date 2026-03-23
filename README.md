# OrbitX - Real-Time Satellite Tracker

<div align="center">

![OrbitX Logo](assets/satellite-logo.ico)

**A high-fidelity satellite tracking application with multi-propagator support, real-time visualization, and multi-satellite tracking**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

</div>

## Features

### Satellite Tracking
- **Live Position Updates** with 500ms refresh and real-time orbital mechanics
- **Multi-Satellite Tracking** - track up to 5 satellites simultaneously with color-coded trajectories
- **10 Satellite Categories** - ISS, Starlink, GPS/Galileo/Beidou, IntelSat, Geosynchronous, CubeSats, Weather, Amateur Radio, Science, Earth Observation
- **Pass Predictions** - calculate visible passes with rise/set times, max elevation, and CSV export
- **87 Observer Locations** worldwide + custom coordinate input

### Multi-Propagator Engine
Choose your orbit prediction method based on accuracy needs:

| Propagator | Accuracy (24h) | Speed | Best For |
|---|---|---|---|
| **SGP4** | ~1-10 km | Instant | General tracking, hobbyists |
| **Numerical (Basic)** | ~1-5 km | ~1s | Better LEO accuracy |
| **Numerical (Standard)** | ~500m-2 km | ~1-2s | Serious tracking |
| **Numerical (High-Fidelity)** | ~10-100 m | ~2-3s | Mission-grade predictions |

**Force models available for numerical propagation:**
- J2-J6 Earth gravity zonal harmonics
- Atmospheric drag (28-layer exponential density model, 0-1000km)
- Solar radiation pressure with cylindrical shadow model
- Third-body perturbations (Sun and Moon)
- Configurable drag coefficient and area-to-mass ratio

### Visualization
- **Global Map** (Plate Carree) with NASA satellite imagery
- **Polar View** (North Polar Stereographic) for polar orbit analysis
- **Dark / Light Theme** - full app theme switching via toggle
- **Ground Footprint** visualization
- **Trajectory Prediction** - 1 hour ahead with configurable resolution
- **Zoom and Pan** with matplotlib navigation toolbar

### User Experience
- **Keyboard Shortcuts** - Space (play/pause), Escape (stop)
- **Persistent Preferences** - theme, location, last satellite saved automatically
- **Data Staleness Indicator** - warns when TLE data is outdated (>48h)
- **Debounced Search** with placeholder text
- **Status Bar** - satellite count, tracking status, data age

## System Requirements

- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8+
- **RAM**: 4 GB minimum
- **Storage**: 500 MB
- **Internet**: Required for satellite data download

### System Dependencies

**macOS:**
```bash
brew install proj geos
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-dev libproj-dev proj-data proj-bin libgeos-dev
```

## Quick Start

### Option 1: Automated Setup
```bash
python3 setup_dev.py
source satellite_env/bin/activate
python3 main.py
```

### Option 2: Manual Setup
```bash
git clone https://github.com/yourusername/satellite-tracker.git
cd satellite-tracker

python3 -m venv satellite_env
source satellite_env/bin/activate   # macOS/Linux
# satellite_env\Scripts\activate    # Windows

pip install -r requirements.txt
python3 main.py
```

## Usage

### First Launch
1. Run the app - it will prompt you to fetch satellite data
2. Select a category (ISS & Space Stations is a good start)
3. Click a satellite in the list to see its position
4. Press **Space** or click **START LIVE TRACKING** for real-time updates

### Multi-Satellite Tracking
- **Double-click** a satellite in the list to add it to the tracking overlay (up to 5)
- Each tracked satellite gets a unique color (cyan, orange, purple, green, rose)
- Double-click again or click **x** to remove from tracking

### Switching Propagators
1. Use the **Propagator** dropdown in the control panel
2. Select **SGP4** (fast) or **Numerical** (accurate)
3. When Numerical is selected, choose a force model preset:
   - **basic** - J2 + drag (fast, good for quick estimates)
   - **standard** - J2, J3 + drag (recommended default)
   - **high_fidelity** - All forces (J2-J6, drag, SRP, Moon, Sun)

### Pass Schedule
1. Select a satellite
2. Click **PASS SCHEDULE**
3. Choose time range (1-30 days) and click **CALCULATE**
4. Export results to CSV

### Observer Location
- Click **SELECT LOCATION** to change your position
- Choose from 87 preset cities or enter custom lat/lon
- Location is saved automatically for next launch

## Architecture

```
OrbitX/
├── main.py                          # Entry point
├── satellite_tracker.py             # UI controller (callbacks, wiring)
├── config.py                        # Theme definitions, constants, locations
│
├── ui/                              # User interface
│   ├── controls.py                  # Buttons, toggles, dialogs, satellite list
│   ├── dashboard.py                 # Telemetry display panel
│   └── map_display.py               # Cartopy map with trajectories
│
└── utils/                           # Backend logic
    ├── data_manager.py              # TLE data lifecycle (load, fetch, save)
    ├── tracking.py                  # Tracking state, trajectory computation
    ├── preferences.py               # User settings persistence (JSON)
    ├── orbit_calc.py                # Public API (propagator facade)
    ├── satellite_data.py            # TLE fetch, parse, validate
    ├── theme.py                     # Shared theme utilities
    ├── resource_utils.py            # PyInstaller path resolution
    └── propagators/                 # Orbit propagation engines
        ├── __init__.py              # PropagatorType, ForceModel config
        ├── base.py                  # Abstract base class + TLE parser
        ├── sgp4_prop.py             # SGP4/SDP4 via Skyfield
        ├── numerical_prop.py        # Cowell's method + RK8 integrator
        └── perturbations.py         # Force models (J2-J6, drag, SRP, 3rd body)
```

### Key Design Decisions
- **Propagator pattern** - swap SGP4/Numerical at runtime without changing UI code
- **Thin controller** - `satellite_tracker.py` only wires callbacks; logic lives in `utils/`
- **Theme system** - every widget accepts a theme dict, supports live switching
- **Data manager** - thread-safe TLE fetching with success/error callbacks

## Dependencies

| Package | Purpose |
|---|---|
| numpy | Numerical computation |
| matplotlib | 2D visualization and map rendering |
| skyfield | SGP4 orbital mechanics |
| cartopy | Geospatial map projections |
| requests | HTTP for TLE data fetching |
| scipy | Numerical integration (RK8) and Cartopy transforms |
| poliastro | Astrodynamics utilities |

## Building Executable

```bash
python3 build.py
```

Or manually:
```bash
pyinstaller --onefile --windowed --icon=assets/satellite-logo.ico \
    --name="OrbitX" \
    --add-data="assets/*:assets/" \
    --hidden-import=skyfield.data \
    --hidden-import=cartopy.feature \
    main.py
```

## Configuration

Edit `config.py` to customize:

```python
# Update frequency
UPDATE_INTERVAL_MS = 500
TRAJECTORY_UPDATE_INTERVAL_S = 10

# Add custom locations
LOCATIONS["My City"] = (latitude, longitude)

# Add custom satellite sources
SATELLITE_CATEGORIES["My Sats"] = "https://celestrak.org/NORAD/elements/gp.php?GROUP=xxx&FORMAT=tle"
```

### Force Model Configuration

```python
from utils.propagators import ForceModel

custom_model = ForceModel(
    j2=True, j3=True, j4=True,
    atmospheric_drag=True,
    solar_radiation_pressure=True,
    third_body_moon=True,
    drag_coefficient=2.2,        # Typical: 2.0-2.5
    area_to_mass_ratio=0.01,     # m^2/kg
)
```

## Troubleshooting

**App won't start:**
```bash
python3 -c "import cartopy, matplotlib, skyfield, scipy"
```

**Blank map:** Install system dependencies (proj, geos) and reinstall cartopy.

**Polar view error:** Ensure scipy is installed (`pip install scipy`).

**Numerical propagator slow:** Use "basic" or "standard" preset instead of "high_fidelity". High-fidelity computes 9 force models per integration step.

**Stale data warning:** Click UPDATE DATA to fetch fresh TLEs. Satellite positions drift ~1-10 km/day with old data.

## License

MIT License - see [LICENSE](LICENSE).

## Acknowledgments

- **Dr. Gibran Javed**
- **Dr. Abdul Majid**
- **Hamza Sultan**

## Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/satellite-tracker/issues)
- **Email**: umersaad9222@gmail.com

---

<div align="center">
<b>OrbitX - Track anything in orbit.</b>
</div>
