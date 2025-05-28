#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for creating a standalone executable of the Water Column Sensor Data Processor
"""

import os
import sys
import platform
import subprocess

# Get platform-specific settings
system = platform.system()
is_windows = system == 'Windows'
is_mac = system == 'Darwin'
is_linux = system == 'Linux'

# Define app name
APP_NAME = "WaterColumnProcessor"

# Determine icon file based on platform
if is_windows:
    icon_path = os.path.abspath(os.path.join('assets', 'app_icon.ico'))
elif is_mac:
    icon_path = os.path.abspath(os.path.join('assets', 'app_icon.icns'))
else:  # Linux
    icon_path = os.path.abspath(os.path.join('assets', 'app_icon.png'))

# Create icon files directory if it doesn't exist
os.makedirs('assets', exist_ok=True)

# Check if icon exists
if not os.path.exists(icon_path):
    print(f"Warning: Icon file {icon_path} not found. Building without an icon.")
    icon_path = None

# Build command options
pyinstaller_options = [
    'pyinstaller',
    '--name={}'.format(APP_NAME),
    '--onedir',  # Create a single executable
    '--windowed',  # No console window
    '--clean',  # Clean PyInstaller cache
    '--noconfirm',  # Overwrite existing build files
]

# extending - sys compatibility
pyinstaller_options.extend([
    '--additional-hooks-dir=.',
    '--hidden-import=numpy',
    '--hidden-import=pandas',
    '--hidden-import=matplotlib',
    '--hidden-import=matplotlib.backends.backend_tkagg',
    f'--add-data=src{os.pathsep}src',  # This properly includes the src directory
    f'--add-data=assets/app_icon.png{os.pathsep}assets',
    f'--add-data=assets/app_icon.icns{os.pathsep}assets'
])

# Add icon if available
if icon_path:
    pyinstaller_options.append('--icon={}'.format(icon_path))

# Add platform-specific options
if is_mac:
    pyinstaller_options.append('--osx-bundle-identifier=com.watercolumn.processor')

# Use the main.py as the entry point
pyinstaller_options.append('main.py')

# Print information
print("Building executable with PyInstaller...")
print(f"Platform: {system}")
print(f"Options: {' '.join(pyinstaller_options)}")

# Run PyInstaller
try:
    subprocess.run(pyinstaller_options, check=True)
    print(f"\nBuild completed successfully! Executable is located in the 'dist' folder.")

    # Show the output location
    dist_path = os.path.abspath('dist')
    if is_windows:
        exe_path = os.path.join(dist_path, f"{APP_NAME}.exe")
        print(f"Executable path: {exe_path}")
    elif is_mac:
        app_path = os.path.join(dist_path, f"{APP_NAME}.app")
        print(f"Application path: {app_path}")
    else:
        bin_path = os.path.join(dist_path, APP_NAME)
        print(f"Binary path: {bin_path}")

except subprocess.CalledProcessError as e:
    print(f"Error during build: {e}")
    sys.exit(1)

# Optional: Create a distributable package
if '--package' in sys.argv:
    print("\nCreating distributable package...")
    if is_windows:
        # Create a ZIP file for Windows
        import zipfile

        zip_path = os.path.join('dist', f"{APP_NAME}_Windows.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(os.path.join('dist', f"{APP_NAME}.exe"), f"{APP_NAME}.exe")
            zipf.write('README.md', 'README.md')
        print(f"Windows package created: {zip_path}")

    elif is_mac:
        # Create a DMG file for macOS (requires create-dmg)
        try:
            dmg_path = os.path.join('dist', f"{APP_NAME}_macOS.dmg")
            subprocess.run([
                'create-dmg',
                '--volname', APP_NAME,
                '--volicon', icon_path if icon_path else 'assets/app_icon.icns',
                '--window-pos', '200', '100',
                '--window-size', '800', '400',
                '--icon-size', '100',
                '--icon', f"{APP_NAME}.app", '200', '200',
                '--hide-extension', f"{APP_NAME}.app",
                '--app-drop-link', '600', '200',
                dmg_path,
                os.path.join('dist', f"{APP_NAME}.app")
            ], check=True)
            print(f"macOS package created: {dmg_path}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Failed to create DMG. create-dmg might not be installed.")
            # Fallback to ZIP
            import zipfile

            zip_path = os.path.join('dist', f"{APP_NAME}_macOS.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Recursively add .app directory
                app_path = os.path.join('dist', f"{APP_NAME}.app")
                for root, dirs, files in os.walk(app_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, 'dist')
                        zipf.write(file_path, arcname)
                zipf.write('README.md', 'README.md')
            print(f"macOS ZIP package created: {zip_path}")

    else:  # Linux
        # Create a tarball for Linux
        import tarfile

        tar_path = os.path.join('dist', f"{APP_NAME}_Linux.tar.gz")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(os.path.join('dist', APP_NAME), arcname=APP_NAME)
            tar.add('README.md', 'README.md')
        print(f"Linux package created: {tar_path}")

print("\nBuild process complete!")