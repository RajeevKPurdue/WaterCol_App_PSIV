# Simple utility functions for the Water Column Sensor Data Processor
# This file is kept minimal since the main functionality is in sensor_processor.py

import os
import sys
import platform
import re


def get_platform_info():
    """Get basic platform information."""
    return {
        "system": platform.system(),
        "version": platform.version(),
        "python": platform.python_version(),
        "architecture": platform.architecture(),
        "is_windows": platform.system() == "Windows",
        "is_mac": platform.system() == "Darwin",
        "is_linux": platform.system() == "Linux",
    }


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    For PyInstaller, the path needs to account for the bundled application structure.
    """
    # Determine if the application is running from a bundled executable
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores the path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        # Running normally
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    return os.path.join(base_path, relative_path)


def extract_depth_from_filename(filename, pattern):
    """Extract depth value from filename using a regex pattern."""
    try:
        match = re.search(pattern, filename)
        if match:
            return float(match.group(1))
        return None
    except Exception:
        return None