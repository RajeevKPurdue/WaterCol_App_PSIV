#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Water Column Sensor Data Processor application.
This script imports the SensorDataProcessor class from the src directory
and initializes the application.
"""

import os
import sys
import tkinter as tk

# Determine if we're running in a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Running in a bundle
    bundle_dir = sys._MEIPASS
    # Add the bundled src directory to the path
    if os.path.exists(os.path.join(bundle_dir, 'src')):
        sys.path.insert(0, os.path.join(bundle_dir, 'src'))
    else:
        # If src not found, add bundle_dir itself
        sys.path.insert(0, bundle_dir)
else:
    # Running in a normal Python environment
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(current_dir, 'src'))

# Now try the import
try:
    # Try direct import first
    from WC_Vars_PSIV import SensorDataProcessor
except ImportError:
    try:
        # Try with src prefix
        from src.WC_Vars_PSIV import SensorDataProcessor
    except ImportError as e:
        print(f"Error: Could not import SensorDataProcessor from WC_Vars_PSIV.py")
        print(f"Exception details: {e}")
        print(f"Current Python path: {sys.path}")

        # Debug more information
        for path in sys.path:
            if os.path.exists(path):
                print(f"Contents of {path}: {os.listdir(path)}")
            else:
                print(f"{path} does not exist")

        sys.exit(1)


def main():
    """Initialize and start the application"""
    # Create the main Tkinter window
    root = tk.Tk()

    # Set window title
    root.title("Water Column Sensor Data Processor")

    # Configure window size
    window_width = 900
    window_height = 700

    # Center the window on the screen
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Make window resizable
    root.resizable(True, True)

    # Set application icon if available
    try:
        # For macOS, use TK iconphoto
        if sys.platform == "darwin":
            img = tk.PhotoImage(file=os.path.join(current_dir, "assets", "app_icon.png"))
            root.iconphoto(True, img)
        # For Windows, use iconbitmap
        elif sys.platform == "win32":
            icon_path = os.path.join(current_dir, "assets", "app_icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
    except Exception as e:
        # Continue without icon if there's an error
        print(f"Warning: Could not set application icon: {e}")

    # Initialize the application
    app = SensorDataProcessor(root)

    # Start the main event loop
    root.mainloop()


if __name__ == "__main__":
    main()