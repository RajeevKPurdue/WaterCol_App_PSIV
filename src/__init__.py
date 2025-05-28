"""
Water Column Sensor Data Processor Package

This package contains the core functionality for the Water Column Sensor
Data Processor application, which processes, interpolates, and visualizes
water column sensor data.
"""

# Import key classes and functions to make them available at the package level
# This is optional but can simplify imports in other parts of your code
try:
    from WC_Vars_PSIVWC_Vars_PSIV import SensorDataProcessor
except ImportError:
    # It's okay if this fails, as the specific import might be handled elsewhere
    pass

# Package metadata
__author__ = "Rajeev Kumar"
__version__ = "1.0.0"