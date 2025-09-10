#!/usr/bin/env python3
"""
Build script for OrbitX Satellite Tracker
Creates standalone executable using PyInstaller
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def get_platform_args():
    """Get platform-specific arguments"""
    system = platform.system()
    args = []
    
    if system == "Windows":
        args.extend([
            "--icon=assets/satellite-logo.ico",
            "--version-file=version_info.txt"  # Optional version info
        ])
    elif system == "Darwin":  # macOS
        args.extend([
            "--icon=assets/satellite-logo.ico",
            "--osx-bundle-identifier=com.orbitx.satellitetracker"
        ])
    else:  # Linux
        args.extend([
            "--icon=assets/satellite-logo.ico"
        ])
    
    return args

def clean_build():
    """Clean previous build artifacts"""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["*.spec"]
    
    print("🧹 Cleaning previous build artifacts...")
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")
    
    for pattern in files_to_clean:
        for file in Path(".").glob(pattern):
            file.unlink()
            print(f"   Removed {file}")

def build_executable(build_type="onefile"):
    """Build the executable"""
    if not check_pyinstaller():
        print("❌ Failed to install PyInstaller")
        return False
    
    print(f"🏗️  Building {build_type} executable...")
    
    # Base arguments
    args = [
        sys.executable, "-m", "PyInstaller",
        "--windowed",  # No console window
        "--name=OrbitX",
        "--clean",  # Clean build
    ]
    
    # Build type
    if build_type == "onefile":
        args.append("--onefile")
    else:
        args.append("--onedir")
    
    # Platform-specific arguments
    args.extend(get_platform_args())
    
    # Data files and hidden imports
    args.extend([
        "--add-data=assets/*;assets/",
        "--add-data=tle.txt;.",
        "--hidden-import=skyfield.data",
        "--hidden-import=skyfield.sgp4lib",
        "--hidden-import=cartopy.feature",
        "--hidden-import=cartopy.crs",
        "--hidden-import=matplotlib.backends.backend_tkagg",
        "--exclude-module=tkinter.test",
        "--exclude-module=PIL.tests",
        "--exclude-module=numpy.tests",
        "main.py"
    ])
    
    # Run PyInstaller
    try:
        result = subprocess.run(args, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        
        # Show output location
        if build_type == "onefile":
            if platform.system() == "Windows":
                executable = "dist/OrbitX.exe"
            else:
                executable = "dist/OrbitX"
        else:
            executable = "dist/OrbitX/"
        
        print(f"📦 Executable location: {os.path.abspath(executable)}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_installer():
    """Create a simple installer script (Windows)"""
    if platform.system() != "Windows":
        print("ℹ️  Installer creation is only supported on Windows")
        return
    
    installer_script = '''
@echo off
echo Installing OrbitX Satellite Tracker...

REM Create installation directory
set INSTALL_DIR=%PROGRAMFILES%\\OrbitX
mkdir "%INSTALL_DIR%" 2>nul

REM Copy executable
copy "OrbitX.exe" "%INSTALL_DIR%\\" >nul
if errorlevel 1 (
    echo Error: Failed to copy files. Run as administrator.
    pause
    exit /b 1
)

REM Create desktop shortcut
set SHORTCUT="%USERPROFILE%\\Desktop\\OrbitX.lnk"
echo Set oWS = WScript.CreateObject("WScript.Shell") > temp_shortcut.vbs
echo Set oLink = oWS.CreateShortcut("%SHORTCUT%") >> temp_shortcut.vbs
echo oLink.TargetPath = "%INSTALL_DIR%\\OrbitX.exe" >> temp_shortcut.vbs
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> temp_shortcut.vbs
echo oLink.Description = "OrbitX Satellite Tracker" >> temp_shortcut.vbs
echo oLink.Save >> temp_shortcut.vbs
cscript temp_shortcut.vbs >nul
del temp_shortcut.vbs

REM Create start menu entry
set STARTMENU="%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"
copy "%SHORTCUT%" "%STARTMENU%\\OrbitX.lnk" >nul

echo.
echo ✅ Installation completed successfully!
echo Desktop shortcut created: OrbitX
echo Start menu entry created
echo Installation directory: %INSTALL_DIR%
echo.
pause
'''
    
    with open("dist/install.bat", "w") as f:
        f.write(installer_script)
    
    print("📦 Created installer script: dist/install.bat")

def main():
    """Main build function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build OrbitX Satellite Tracker")
    parser.add_argument("--type", choices=["onefile", "onedir"], default="onefile",
                       help="Build type (default: onefile)")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts first")
    parser.add_argument("--installer", action="store_true", help="Create installer (Windows only)")
    
    args = parser.parse_args()
    
    print("🚀 OrbitX Build Script")
    print("=" * 50)
    
    if args.clean:
        clean_build()
    
    success = build_executable(args.type)
    
    if success and args.installer:
        create_installer()
    
    if success:
        print("\n🎉 Build process completed!")
        
        # Show file sizes
        if args.type == "onefile":
            exe_path = "dist/OrbitX.exe" if platform.system() == "Windows" else "dist/OrbitX"
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📏 Executable size: {size_mb:.1f} MB")
    else:
        print("\n💥 Build process failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()