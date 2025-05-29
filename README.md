# Water Column Sensor Data Processor - Desktop Application

This is a desktop application for processing, interpolating, and visualizing water column sensor data from .txt and .csv files.

## Features

- Import and process sensor data files
- Interpolate data across depths
- Generate 2D visualizations of 1D water column data
- Export plots and processed data

## Installation

### Option 1: Run the executable (simplest)

1. Download the latest release for your operating system from the releases page
2. Extract the zip/tar file
3. Run the executable file:
   - Windows: `WaterColumnProcessor.exe`
   - macOS: `WaterColumnProcessor.app`
   - Linux: `WaterColumnProcessor`

### Option 2: Build from source

1. Clone this repository
2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
3. Run the build script:
   ```
   python build_app.py
   ```
4. The executable will be created in the `dist` folder

## Usage

1. **Data Import**:
   - Select sensor data files (.txt or .csv)
   - Configure header detection and depth extraction
   

2. **Data Processing**:
   - Select variables to process (includes your DateTime index column)
   - Set time index and resampling options
   - - Can assess and check your sensor depths manually if depths are not read from filenames

3. **Interpolation**:
   - Set depth resolution and maximum depth
   - Choose variables to interpolate

4. **Visualization**:
   - Create contour plots of the interpolated data
   - Customize plot appearance
   - Export plots to various formats

## System Requirements

- Windows 7 or later
- macOS 10.13 or later
- Linux (most modern distributions)
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space

## Citation
If you use this software in your research, please cite:

Kumar, R. (2025). WaterCol_App_PSIV: Application to Process, Summarize, Interpolate, and Visualize water column sensor data. GitHub. https://github.com/RajeevKPurdue/WaterCol_App_PSIV

Or in academic format:
Kumar, R. (2025). WaterCol_App_PSIV: Application to Process, Summarize, Interpolate, and Visualize water column sensor data. Software. GitHub repository. https://github.com/RajeevKPurdue/WaterCol_App_PSIV

## License
This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

## Acknowledgments
If you use this code in published work, please acknowledge its use and cite any relevant publications.
## Acknowledgments

If you use this code in published work, please acknowledge its use and cite any relevant publications.
