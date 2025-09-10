# OrbitX - Real-Time Satellite Tracker

<div align="center">

![OrbitX Logo](assets/satellite-logo.ico)

**A sophisticated desktop application for real-time satellite tracking with interactive visualization**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()


</div>

## 🚀 Features

### 🛰️ Real-Time Satellite Tracking
- **Live Position Calculation**: Real-time satellite position updates using precise orbital mechanics
- **Multiple Satellite Categories**: Track IntelSat, Starlink, GPS/Galileo/Beidou, Geosynchronous, and CubeSat constellations
- **Trajectory Prediction**: Visualize future satellite paths with configurable time intervals
- **Pass Predictions**: Calculate when satellites will be visible from your location
- **Real-Time Updates**: Live satellite markers with orbital trajectories
- **Footprint Display**: Satellite ground coverage visualization


## 📋 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **RAM**: 4 GB minimum, 8 GB recommended
- **Storage**: 500 MB for application and dependencies
- **Internet**: Required for initial satellite data download or updating to latest data

### Additional System Dependencies

#### Windows
- Visual C++ Redistributable (usually pre-installed)
- Windows Defender may require manual approval for executable

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install python3-dev python3-pip
sudo apt-get install libproj-dev proj-data proj-bin libgeos-dev
sudo apt-get install libffi-dev libssl-dev
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install proj geos
```

## 🔧 Installation

### Method 1: Run from Source (Recommended for Development)

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/satellite-tracker.git
cd satellite-tracker
```

2. **Create Virtual Environment**
```bash
python -m venv satellite_env

# Windows
satellite_env\Scripts\activate

# macOS/Linux
source satellite_env/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the Application**
```bash
python main.py
```

### Method 2: Install as Package

```bash
pip install git+https://github.com/yourusername/satellite-tracker.git
satellite-tracker
```

## 🏗️ Building Executable

To create a standalone executable that doesn't require Python installation:

### Prerequisites
```bash
pip install pyinstaller
```

### Build Process

#### Windows Executable
```bash
# Single file executable (slower startup, portable)
pyinstaller --onefile --windowed --icon=assets/satellite-logo.ico --name="OrbitX" main.py

# Directory distribution (faster startup)
pyinstaller --onedir --windowed --icon=assets/satellite-logo.ico --name="OrbitX" main.py
```

#### Linux/macOS Executable
```bash
# Single file executable
pyinstaller --onefile --windowed --icon=assets/satellite-logo.ico --name="OrbitX" main.py

# App bundle (macOS)
pyinstaller --onedir --windowed --icon=assets/satellite-logo.ico --name="OrbitX" main.py
```

### Advanced Build Options

For a more optimized build with better compatibility:

```bash
pyinstaller --onefile \
    --windowed \
    --icon=assets/satellite-logo.ico \
    --name="OrbitX" \
    --add-data="assets/*;assets/" \
    --add-data="tle.txt;." \
    --hidden-import=skyfield.data \
    --hidden-import=cartopy.feature \
    --exclude-module=tkinter.test \
    main.py
```

### Build Script

Create a `build.py` script for automated building:

```python
import PyInstaller.__main__
import sys
import os

def build_executable():
    args = [
        '--onefile',
        '--windowed',
        '--icon=assets/satellite-logo.ico',
        '--name=OrbitX',
        '--add-data=assets/*;assets/',
        '--add-data=tle.txt;.',
        '--hidden-import=skyfield.data',
        '--hidden-import=cartopy.feature',
        '--exclude-module=tkinter.test',
        'main.py'
    ]
    
    PyInstaller.__main__.run(args)

if __name__ == "__main__":
    build_executable()
```

Run with: `python build.py`

## 📖 Usage Guide

### First Launch

1. **Start the Application**
   - Run `python main.py` or launch the executable
   - The application will load with a default satellite selection

2. **Update Satellite Data**
   - Click "🔄 UPDATE DATA" to fetch the latest satellite information
   - Select a satellite category (Starlink, GPS, etc.)
   - Wait for the download to complete

### Basic Operations

#### Selecting Satellites
- Use the search box to filter satellites by name
- Click on any satellite in the list to start tracking
- The map will center on the selected satellite

#### Map Navigation
- **Zoom**: Use mouse wheel or toolbar buttons
- **Pan**: Click and drag to move the map
- **Reset View**: Double-click to reset zoom level

#### View Modes
- **Global View**: Standard world map projection
- **Polar View**: Arctic/Antarctic centered view (useful for polar orbits)
- **Light/Dark Mode**: Toggle between NASA day/night imagery

#### Location Settings
- Click "📍 SELECT LOCATION" to change your observer position
- Choose from predefined cities or enter custom coordinates
- This affects satellite pass predictions and elevation angles

### Advanced Features

#### Live Tracking
- Click "⏵ LIVE TRACKING" to enable real-time updates
- Satellite position updates every 500ms
- Click "⏸ PAUSE" to stop live updates

#### Satellite Passes
- Click "📅 SCHEDULE" to view upcoming passes
- Select time range (1-30 days)
- Export schedule to CSV for external use

#### Data Export
- Schedule data can be exported as CSV files
- Files include rise/set times, azimuths, and pass duration
- Saved to the application directory

## 🔧 Configuration

### Customizing Settings

Edit `config.py` to modify:

```python
# Update intervals (milliseconds)
UPDATE_INTERVAL = 500

# Color scheme
DARK_BG = "#0B1426"
ACCENT_COLOR = "#00b4d8"

# Add custom locations
LOCATIONS["My Location"] = (latitude, longitude)

# Add custom satellite sources
SATELLITE_CATEGORIES["Custom"] = "https://example.com/tle-data.txt"
```

### Data Sources

The application fetches TLE (Two-Line Element) data from celestrak.org:
- **IntelSat**: Commercial communication satellites
- **Starlink**: SpaceX internet constellation
- **GNSS**: GPS, Galileo, BeiDou navigation satellites
- **Geosynchronous**: Active geostationary satellites
- **CubeSats**: Small research satellites

## 🐛 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check for missing system libraries
python -c "import cartopy, matplotlib, skyfield"
```

#### Map Display Issues
- **Blank Map**: Install cartopy dependencies
- **Slow Rendering**: Reduce update frequency in config.py
- **Memory Issues**: Close other applications, increase system RAM

#### Network/Data Issues
```bash
# Test internet connectivity
python -c "import requests; print(requests.get('https://celestrak.org').status_code)"

# Clear cached data
rm -rf ~/skyfield-data/*  # Linux/macOS
del %USERPROFILE%\skyfield-data\*  # Windows
```

#### Build Issues

**PyInstaller Problems:**
```bash
# Clean build
pyinstaller --clean main.spec

# Verbose output for debugging
pyinstaller --log-level DEBUG main.py
```

**Missing Dependencies:**
```bash
# Manually add missing modules
pyinstaller --hidden-import=missing_module main.py
```

### Performance Optimization

#### For Better Performance:
- Disable live tracking when not needed
- Reduce trajectory point count in `config.py`
- Use polar view for high-latitude satellites
- Close other memory-intensive applications

#### For Lower Resource Usage:
```python
# In config.py
UPDATE_INTERVAL = 1000  # Slower updates
TRAJECTORY_POINTS = 60  # Fewer trajectory points
```

## 📁 Project Structure

```
satellite-tracker/
├── main.py                 # Application entry point
├── satellite_tracker.py    # Main application class
├── config.py              # Configuration and constants
├── requirements.txt       # Python dependencies
├── tle.txt               # Cached satellite data
├── assets/               # Images and icons
│   ├── satellite-logo.ico
│   ├── nasa_dark.jpg
│   ├── nasa_light.jpg
│   └── satellite.webp
├── ui/                   # User interface components
│   ├── __init__.py
│   ├── controls.py       # Control panels and dialogs
│   ├── dashboard.py      # Satellite data display
│   └── map_display.py    # Map visualization
└── utils/                # Utility modules
    ├── __init__.py
    ├── orbit_calc.py     # Orbital mechanics
    ├── resource_utils.py # Resource path management
    └── satellite_data.py # TLE data handling
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with detailed description

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
pytest tests/

# Format code
black satellite_tracker/ ui/ utils/

# Lint code
flake8 satellite_tracker/ ui/ utils/
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Special Thanks  
- **Dr. Gibran Javed**  
- **Dr. Abdul Majid**
- **Hamza Sultan**

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/satellite-tracker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/satellite-tracker/discussions)
- **Email**: umersaad9222@gmail.com

---

<div align="center">
<b>Happy Satellite Tracking! 🛰️</b>
</div>
