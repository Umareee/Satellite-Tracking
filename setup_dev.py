#!/usr/bin/env python3
"""
Development environment setup script for OrbitX Satellite Tracker
"""

import os
import sys
import subprocess
import platform
import venv
from pathlib import Path

def run_command(command, description, check=True):
    """Run a command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            return True
        else:
            print(f"⚠️  {description} completed with warnings")
            if result.stderr:
                print(f"   Warning: {result.stderr.strip()}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   Required: Python 3.8 or higher")
        return False

def install_system_dependencies():
    """Install system dependencies based on platform"""
    system = platform.system()
    
    if system == "Linux":
        print("🐧 Installing Linux system dependencies...")
        distro = platform.linux_distribution()[0].lower() if hasattr(platform, 'linux_distribution') else "unknown"
        
        if "ubuntu" in distro or "debian" in distro:
            commands = [
                "sudo apt-get update",
                "sudo apt-get install -y python3-dev python3-pip",
                "sudo apt-get install -y libproj-dev proj-data proj-bin libgeos-dev",
                "sudo apt-get install -y libffi-dev libssl-dev",
                "sudo apt-get install -y python3-tk"
            ]
        elif "fedora" in distro or "rhel" in distro or "centos" in distro:
            commands = [
                "sudo dnf update -y",
                "sudo dnf install -y python3-devel python3-pip",
                "sudo dnf install -y proj-devel geos-devel",
                "sudo dnf install -y libffi-devel openssl-devel",
                "sudo dnf install -y python3-tkinter"
            ]
        else:
            print("   Manual installation required for your Linux distribution")
            print("   Please install: python3-dev, libproj-dev, libgeos-dev, python3-tk")
            return True
        
        success = True
        for cmd in commands:
            if not run_command(cmd, f"Running: {cmd}", check=False):
                success = False
        return success
        
    elif system == "Darwin":  # macOS
        print("🍎 Installing macOS system dependencies...")
        # Check if Homebrew is installed
        homebrew_check = subprocess.run("which brew", shell=True, capture_output=True)
        if homebrew_check.returncode != 0:
            print("   Homebrew not found. Please install it first:")
            print('   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
            return False
        
        commands = [
            "brew update",
            "brew install proj geos",
            "brew install python-tk"
        ]
        
        success = True
        for cmd in commands:
            if not run_command(cmd, f"Running: {cmd}", check=False):
                success = False
        return success
        
    elif system == "Windows":
        print("🪟 Windows detected - most dependencies will be installed via pip")
        return True
    
    else:
        print(f"⚠️  Unknown system: {system}")
        return True

def create_virtual_environment():
    """Create a virtual environment"""
    venv_path = Path("satellite_env")
    
    if venv_path.exists():
        print("📁 Virtual environment already exists")
        return str(venv_path)
    
    print("📦 Creating virtual environment...")
    try:
        venv.create(venv_path, with_pip=True)
        print("✅ Virtual environment created: satellite_env/")
        return str(venv_path)
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return None

def get_venv_python(venv_path):
    """Get the path to Python executable in virtual environment"""
    system = platform.system()
    if system == "Windows":
        return str(Path(venv_path) / "Scripts" / "python.exe")
    else:
        return str(Path(venv_path) / "bin" / "python")

def install_python_dependencies(python_exe):
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    # Upgrade pip first
    run_command(f'"{python_exe}" -m pip install --upgrade pip', "Upgrading pip")
    
    # Install requirements
    if Path("requirements.txt").exists():
        success = run_command(f'"{python_exe}" -m pip install -r requirements.txt', 
                            "Installing requirements.txt")
    else:
        # Fallback to manual installation
        packages = [
            "numpy>=1.24.0",
            "matplotlib>=3.7.0",
            "skyfield>=1.46.0",
            "cartopy>=0.21.0",
            "requests>=2.28.0"
        ]
        
        success = True
        for package in packages:
            if not run_command(f'"{python_exe}" -m pip install "{package}"', 
                             f"Installing {package}"):
                success = False
    
    return success

def install_development_tools(python_exe):
    """Install development tools"""
    print("🛠️  Installing development tools...")
    
    dev_packages = [
        "pyinstaller",  # For building executables
        "pytest",       # For testing
        "black",        # Code formatter
        "flake8",       # Linter
        "mypy"          # Type checker
    ]
    
    success = True
    for package in dev_packages:
        if not run_command(f'"{python_exe}" -m pip install {package}', 
                         f"Installing {package}", check=False):
            success = False
    
    return success

def test_installation(python_exe):
    """Test if the installation works"""
    print("🧪 Testing installation...")
    
    test_script = '''
import sys
try:
    import numpy
    import matplotlib
    import skyfield
    import cartopy
    import requests
    import tkinter
    print("✅ All dependencies imported successfully")
    sys.exit(0)
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
'''
    
    with open("test_imports.py", "w") as f:
        f.write(test_script)
    
    success = run_command(f'"{python_exe}" test_imports.py', "Testing imports")
    
    # Clean up
    Path("test_imports.py").unlink(missing_ok=True)
    
    return success

def create_run_scripts(venv_path):
    """Create convenience scripts to run the application"""
    system = platform.system()
    
    if system == "Windows":
        # Windows batch script
        script_content = f'''@echo off
call "{venv_path}\\Scripts\\activate"
python main.py
pause
'''
        with open("run_orbitx.bat", "w") as f:
            f.write(script_content)
        print("✅ Created run_orbitx.bat")
        
    else:
        # Unix shell script
        script_content = f'''#!/bin/bash
source "{venv_path}/bin/activate"
python main.py
'''
        with open("run_orbitx.sh", "w") as f:
            f.write(script_content)
        Path("run_orbitx.sh").chmod(0o755)  # Make executable
        print("✅ Created run_orbitx.sh")

def print_next_steps(venv_path):
    """Print next steps for the user"""
    system = platform.system()
    
    print("\n🎉 Setup completed successfully!")
    print("=" * 50)
    print("\n📋 Next steps:")
    print("1. Activate the virtual environment:")
    
    if system == "Windows":
        print(f"   {venv_path}\\Scripts\\activate")
        print("\n2. Run the application:")
        print("   python main.py")
        print("   OR double-click run_orbitx.bat")
    else:
        print(f"   source {venv_path}/bin/activate")
        print("\n2. Run the application:")
        print("   python main.py")
        print("   OR ./run_orbitx.sh")
    
    print("\n3. Build executable (optional):")
    print("   python build.py")
    
    print("\n📖 Additional commands:")
    print("   python build.py --help     # Build options")
    print("   pytest tests/             # Run tests (if available)")
    print("   black .                   # Format code")
    print("   flake8 .                  # Lint code")

def main():
    """Main setup function"""
    print("🚀 OrbitX Development Environment Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install system dependencies
    if not install_system_dependencies():
        print("⚠️  Some system dependencies may not have been installed")
        print("   The setup will continue, but you may need to install them manually")
    
    # Create virtual environment
    venv_path = create_virtual_environment()
    if not venv_path:
        sys.exit(1)
    
    # Get Python executable path
    python_exe = get_venv_python(venv_path)
    
    # Install Python dependencies
    if not install_python_dependencies(python_exe):
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Install development tools
    if not install_development_tools(python_exe):
        print("⚠️  Some development tools may not have been installed")
    
    # Test installation
    if not test_installation(python_exe):
        print("❌ Installation test failed")
        sys.exit(1)
    
    # Create run scripts
    create_run_scripts(venv_path)
    
    # Print next steps
    print_next_steps(venv_path)

if __name__ == "__main__":
    main()