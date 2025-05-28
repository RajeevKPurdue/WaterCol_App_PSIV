from setuptools import setup
import sys
import os

# Use cx_Freeze for building executable
from cx_Freeze import setup, Executable

# Path to application icon
base_dir = os.path.dirname(os.path.abspath(__file__))
if sys.platform == "win32":
    icon = os.path.join(base_dir, "assets", "app_icon.ico")
elif sys.platform == "darwin":
    icon = os.path.join(base_dir, "assets", "app_icon.icns")
else:
    icon = os.path.join(base_dir, "assets", "app_icon.png")

# Set base for GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"

options = {
    "build_exe": {
        "packages": ["tkinter", "matplotlib", "numpy", "pandas"],
        "include_files": [],
        "excludes": ["PyQt5", "PyQt6", "PySide2", "PySide6", "tkinter.test"],
    }
}

executables = [
    Executable(
        "src/sensor_processor.py",
        base=base,
        icon=icon,
        target_name="WaterColumnProcessor",
        shortcut_name="WC Sensor Data PSIV",
        shortcut_dir="DesktopFolder",
    )
]

setup(
    name="WaterColumnProcessor",
    version="1.0.0",
    description="Process, Summarize timescale, Interpolate, & Visualize (PSIV) water column sensor data",
    author="Rajeev Kumar 05/19/2025",
    author_email="<kumar478@purdue.edu>, <rajeevkbusiness@gmail.com>",
    options=options,
    executables=executables,
)