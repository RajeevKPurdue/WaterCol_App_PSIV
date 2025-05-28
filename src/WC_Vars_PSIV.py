#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Water Column Sensor Data Processor - Final Version

A generalized application for processing sensor data from water column deployments.
Key features:
1. Process sensor .txt files with user-selected variables
2. Split data into separate time series by depth
3. Interpolate data using linear weighted average approach
4. Fill values above/below sensor range (optional)
5. Plot interpolated 2D arrays with customizable visualization options

@author: Based on code by Rajeev Kumar
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple, Optional, Union, Callable
import matplotlib.dates as mdates
import traceback


class SensorDataProcessor:
    def __init__(self, master):
        self.master = master
        self.master.title("Water Column Sensor Data Processor")
        self.master.geometry("900x700")

        # Data storage
        self.input_files = []
        self.processed_dfs = {}
        self.sensor_depths = {}
        self.depth_arrays = {}
        self.interpolated_arrays = {}
        self.current_figure = None

        # Create the main notebook for tabs
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.create_data_import_tab()
        self.create_processing_tab()
        self.create_interpolation_tab()
        self.create_visualization_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(master, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_data_import_tab(self):
        """Create the data import tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="1. Data Import")

        # File selection frame
        file_frame = ttk.LabelFrame(tab, text="Select Input Files")
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Buttons for file operations
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Select Files", command=self.select_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Select Directory", command=self.select_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Selection", command=self.clear_selection).pack(side=tk.LEFT, padx=5)

        # File listbox
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(list_frame, height=10, width=80, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # Parameters for data loading
        param_frame = ttk.LabelFrame(tab, text="Data Import Parameters")
        param_frame.pack(fill=tk.X, padx=10, pady=10)

        # Skip rows detection method
        ttk.Label(param_frame, text="Header Detection:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.header_detection = tk.StringVar(value="auto")
        ttk.Radiobutton(param_frame, text="Auto (find first line with commas)",
                        variable=self.header_detection, value="auto").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(param_frame, text="Fixed line number",
                        variable=self.header_detection, value="fixed").grid(row=0, column=2, sticky=tk.W)

        # Fixed skip lines input
        ttk.Label(param_frame, text="Skip lines (if fixed):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.skip_lines = tk.IntVar(value=8)
        ttk.Entry(param_frame, textvariable=self.skip_lines, width=5).grid(row=1, column=1, sticky=tk.W)

        # Skip units row checkbox
        self.skip_units = tk.BooleanVar(value=True)
        ttk.Checkbutton(param_frame, text="Skip units row after header",
                        variable=self.skip_units).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Sensor depth extraction
        depth_frame = ttk.LabelFrame(tab, text="Sensor Depth Extraction")
        depth_frame.pack(fill=tk.X, padx=10, pady=10)

        # Depth extraction method
        ttk.Label(depth_frame, text="Extract depths from:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.depth_extraction = tk.StringVar(value="filename")
        ttk.Radiobutton(depth_frame, text="Filename (containing depth value)",
                        variable=self.depth_extraction, value="filename").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(depth_frame, text="Manual entry",
                        variable=self.depth_extraction, value="manual").grid(row=0, column=2, sticky=tk.W)

        # Filename pattern for depth
        ttk.Label(depth_frame, text="Filename pattern:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.filename_pattern = tk.StringVar(value=r".*_(\d+\.\d+)_.*")
        ttk.Entry(depth_frame, textvariable=self.filename_pattern, width=30).grid(row=1, column=1, columnspan=2,
                                                                                  sticky=tk.W + tk.E)

        # Preview and load button
        ttk.Button(tab, text="Preview Files", command=self.preview_files).pack(pady=10)
        ttk.Button(tab, text="Load Selected Files", command=self.load_files).pack(pady=10)

    def create_processing_tab(self):
        """Create the data processing tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="2. Data Processing")

        # Variable selection frame
        var_frame = ttk.LabelFrame(tab, text="Select Variables to Process")
        var_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Available and selected variables listboxes
        list_frame = ttk.Frame(var_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(list_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(left_frame, text="Available Variables:").pack(anchor=tk.W)
        scrollbar1 = ttk.Scrollbar(left_frame)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
        self.available_vars = tk.Listbox(left_frame, height=10, width=30, yscrollcommand=scrollbar1.set,
                                         selectmode=tk.MULTIPLE)
        self.available_vars.pack(fill=tk.BOTH, expand=True)
        scrollbar1.config(command=self.available_vars.yview)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text=">>", command=self.add_variables).pack(pady=5)
        ttk.Button(btn_frame, text="<<", command=self.remove_variables).pack(pady=5)

        right_frame = ttk.Frame(list_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(right_frame, text="Selected Variables:").pack(anchor=tk.W)
        scrollbar2 = ttk.Scrollbar(right_frame)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_vars = tk.Listbox(right_frame, height=10, width=30, yscrollcommand=scrollbar2.set,
                                        selectmode=tk.MULTIPLE)
        self.selected_vars.pack(fill=tk.BOTH, expand=True)
        scrollbar2.config(command=self.selected_vars.yview)

        # Column renaming frame
        rename_frame = ttk.LabelFrame(tab, text="Rename Variables (Optional)")
        rename_frame.pack(fill=tk.X, padx=10, pady=10)

        self.rename_vars = {}
        self.rename_entries = {}
        self.rename_container = ttk.Frame(rename_frame)
        self.rename_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Data type conversion frame
        dtype_frame = ttk.LabelFrame(tab, text="Data Type Conversion")
        dtype_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(dtype_frame, text="Numeric columns:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.numeric_cols = tk.StringVar(value="Battery,Temperature,Dissolved Oxygen,Dissolved Oxygen Saturation,Q")
        ttk.Entry(dtype_frame, textvariable=self.numeric_cols, width=50).grid(row=0, column=1, sticky=tk.W + tk.E,
                                                                              padx=5, pady=5)
        ttk.Label(dtype_frame, text="Comma-separated list").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        ttk.Label(dtype_frame, text="DateTime columns:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.datetime_cols = tk.StringVar(value="UTC_Date_&_Time,Eastern Standard Time")
        ttk.Entry(dtype_frame, textvariable=self.datetime_cols, width=50).grid(row=1, column=1, sticky=tk.W + tk.E,
                                                                               padx=5, pady=5)

        # Time aggregation frame
        time_frame = ttk.LabelFrame(tab, text="Time Aggregation")
        time_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(time_frame, text="Time index column:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.time_index = tk.StringVar(value="Eastern Standard Time")
        ttk.Entry(time_frame, textvariable=self.time_index, width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(time_frame, text="Resample frequency:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.resample_freq = tk.StringVar(value="H")
        freqs = ["h", "D", "15min", "6H", "12H", "W", "None"]
        ttk.Combobox(time_frame, textvariable=self.resample_freq, values=freqs, width=10).grid(row=1, column=1,
                                                                                               sticky=tk.W, padx=5,
                                                                                               pady=5)
        ttk.Label(time_frame, text="h=hourly, D=daily, None=no resampling").grid(row=1, column=2, sticky=tk.W, padx=5,
                                                                                 pady=5)

        ttk.Label(time_frame, text="Resample method:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.resample_method = tk.StringVar(value="mean")
        methods = ["mean", "median", "max", "min", "first", "last"]
        ttk.Combobox(time_frame, textvariable=self.resample_method, values=methods, width=10).grid(row=2, column=1,
                                                                                                   sticky=tk.W, padx=5,
                                                                                                   pady=5)

        # Process button
        ttk.Button(tab, text="Process Data", command=self.process_data).pack(pady=10)

    def create_interpolation_tab(self):
        """Create the interpolation tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="3. Interpolation")

        # Interpolation settings frame
        interp_frame = ttk.LabelFrame(tab, text="Interpolation Settings")
        interp_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Depth resolution
        ttk.Label(interp_frame, text="Depth resolution (meters):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.depth_resolution = tk.DoubleVar(value=0.1)
        ttk.Entry(interp_frame, textvariable=self.depth_resolution, width=8).grid(row=0, column=1, sticky=tk.W, padx=5,
                                                                                  pady=5)

        # Max depth
        ttk.Label(interp_frame, text="Maximum depth (meters):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_depth = tk.DoubleVar(value=30.0)
        ttk.Entry(interp_frame, textvariable=self.max_depth, width=8).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Fill values above/below
        self.fill_values = tk.BooleanVar(value=True)
        ttk.Checkbutton(interp_frame, text="Fill values above shallowest/below deepest sensor",
                        variable=self.fill_values).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Interpolation variables
        ttk.Label(interp_frame, text="Variables to interpolate:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.interp_vars_container = ttk.Frame(interp_frame)
        self.interp_vars_container.grid(row=4, column=0, columnspan=2, sticky=tk.W + tk.E, padx=5, pady=5)

        # Preview depths button
        ttk.Button(tab, text="Preview Sensor Depths", command=self.preview_depths).pack(pady=10)
        ttk.Button(tab, text="Edit Sensor Depths", command=self.edit_sensor_depths).pack(pady=10)

        # Interpolation button
        ttk.Button(tab, text="Perform Interpolation", command=self.perform_interpolation).pack(pady=10)

    def create_visualization_tab(self):
        """Create the visualization tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="4. Visualization")

        # Variable selection frame
        var_frame = ttk.LabelFrame(tab, text="Select Variable to Visualize")
        var_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(var_frame, text="Variable:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.viz_variable = tk.StringVar()
        self.viz_var_combo = ttk.Combobox(var_frame, textvariable=self.viz_variable, width=20)
        self.viz_var_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # Plot settings frame
        plot_frame = ttk.LabelFrame(tab, text="Plot Settings")
        plot_frame.pack(fill=tk.X, padx=10, pady=10)

        # Title and labels
        ttk.Label(plot_frame, text="Plot Title:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.plot_title = tk.StringVar()
        ttk.Entry(plot_frame, textvariable=self.plot_title, width=40).grid(row=0, column=1, sticky=tk.W + tk.E, padx=5,
                                                                           pady=5)

        ttk.Label(plot_frame, text="X-Axis Label:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.x_label = tk.StringVar(value="Time")
        ttk.Entry(plot_frame, textvariable=self.x_label, width=40).grid(row=1, column=1, sticky=tk.W + tk.E, padx=5,
                                                                        pady=5)

        ttk.Label(plot_frame, text="Y-Axis Label:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.y_label = tk.StringVar(value="Depth (m)")
        ttk.Entry(plot_frame, textvariable=self.y_label, width=40).grid(row=2, column=1, sticky=tk.W + tk.E, padx=5,
                                                                        pady=5)

        # Color map
        ttk.Label(plot_frame, text="Color Map:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.colormap = tk.StringVar(value="viridis")
        cmaps = ["viridis", "plasma", "inferno", "magma", "cividis", "Spectral", "seismic", "coolwarm", "RdYlBu"]
        ttk.Combobox(plot_frame, textvariable=self.colormap, values=cmaps, width=15).grid(row=3, column=1, sticky=tk.W,
                                                                                          padx=5, pady=5)

        # Figure size
        ttk.Label(plot_frame, text="Figure Size (width, height):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        size_frame = ttk.Frame(plot_frame)
        size_frame.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

        self.fig_width = tk.DoubleVar(value=12.0)
        ttk.Entry(size_frame, textvariable=self.fig_width, width=5).pack(side=tk.LEFT)
        ttk.Label(size_frame, text=" x ").pack(side=tk.LEFT)
        self.fig_height = tk.DoubleVar(value=8.0)
        ttk.Entry(size_frame, textvariable=self.fig_height, width=5).pack(side=tk.LEFT)

        # Font settings
        ttk.Label(plot_frame, text="Font Size:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.font_size = tk.IntVar(value=12)
        ttk.Entry(plot_frame, textvariable=self.font_size, width=5).grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(plot_frame, text="Font Family:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.font_family = tk.StringVar(value="sans-serif")
        fonts = ["sans-serif", "serif", "monospace"]
        ttk.Combobox(plot_frame, textvariable=self.font_family, values=fonts, width=15).grid(row=6, column=1,
                                                                                             sticky=tk.W, padx=5,
                                                                                             pady=5)

        # Normalization
        ttk.Label(plot_frame, text="Normalization:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
        self.normalization = tk.StringVar(value="auto")
        norms = ["auto", "manual"]
        ttk.Combobox(plot_frame, textvariable=self.normalization, values=norms, width=15).grid(row=7, column=1,
                                                                                               sticky=tk.W, padx=5,
                                                                                               pady=5)

        # Manual normalization limits
        limit_frame = ttk.Frame(plot_frame)
        limit_frame.grid(row=8, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        ttk.Label(limit_frame, text="Min:").pack(side=tk.LEFT, padx=5)
        self.norm_min = tk.DoubleVar(value=0.0)
        ttk.Entry(limit_frame, textvariable=self.norm_min, width=8).pack(side=tk.LEFT, padx=5)

        ttk.Label(limit_frame, text="Max:").pack(side=tk.LEFT, padx=5)
        self.norm_max = tk.DoubleVar(value=1.0)
        ttk.Entry(limit_frame, textvariable=self.norm_max, width=8).pack(side=tk.LEFT, padx=5)

        # Time tick settings
        ttk.Label(plot_frame, text="Time Ticks Format:").grid(row=9, column=0, sticky=tk.W, padx=5, pady=5)
        self.time_format = tk.StringVar(value="%Y-%m-%d")
        formats = ["%Y-%m-%d", "%m/%d/%Y", "%b %d", "%B %d, %Y", "%Y-%m-%d %H:%M"]
        ttk.Combobox(plot_frame, textvariable=self.time_format, values=formats, width=15).grid(row=9, column=1,
                                                                                               sticky=tk.W, padx=5,
                                                                                               pady=5)

        ttk.Label(plot_frame, text="Number of Time Ticks:").grid(row=10, column=0, sticky=tk.W, padx=5, pady=5)
        self.num_ticks = tk.IntVar(value=10)
        ttk.Entry(plot_frame, textvariable=self.num_ticks, width=5).grid(row=10, column=1, sticky=tk.W, padx=5, pady=5)

        # Invert y-axis
        self.invert_y = tk.BooleanVar(value=True)
        ttk.Checkbutton(plot_frame, text="Invert Y-Axis (depth increases downward)",
                        variable=self.invert_y).grid(row=11, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Plot button
        ttk.Button(tab, text="Generate Plot", command=self.generate_plot).pack(pady=10)

        # Save options frame
        save_frame = ttk.LabelFrame(tab, text="Save Options")
        save_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(save_frame, text="Save Format:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.save_format = tk.StringVar(value="png")
        formats = ["png", "jpg", "pdf", "svg"]
        ttk.Combobox(save_frame, textvariable=self.save_format, values=formats, width=10).grid(row=0, column=1,
                                                                                               sticky=tk.W, padx=5,
                                                                                               pady=5)

        ttk.Label(save_frame, text="DPI:").grid(row=0, column=2, sticky=tk.W, padx=15, pady=5)
        self.save_dpi = tk.IntVar(value=300)
        ttk.Entry(save_frame, textvariable=self.save_dpi, width=5).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        ttk.Button(save_frame, text="Save Current Plot", command=self.save_plot).grid(row=1, column=0, columnspan=4,
                                                                                      pady=10)

    def select_files(self):
        """Select sensor data files"""
        files = filedialog.askopenfilenames(
            title="Select Sensor Data Files",
            filetypes=(("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*"))
        )

        if files:
            self.input_files = list(files)
            self.update_file_listbox()
            self.status_var.set(f"Selected {len(files)} files")

    def select_directory(self):
        """Select directory containing sensor data files"""
        directory = filedialog.askdirectory(title="Select Directory with Sensor Data Files")

        if directory:
            files = []
            for file in os.listdir(directory):
                if file.lower().endswith(('.txt', '.csv')):
                    files.append(os.path.join(directory, file))

            if files:
                self.input_files = files
                self.update_file_listbox()
                self.status_var.set(f"Found {len(files)} files in directory")
            else:
                messagebox.showinfo("No Files Found", "No .txt or .csv files found in the selected directory.")

    def clear_selection(self):
        """Clear selected files"""
        self.input_files = []
        self.update_file_listbox()
        self.status_var.set("File selection cleared")

    def update_file_listbox(self):
        """Update the file listbox with selected files"""
        self.file_listbox.delete(0, tk.END)
        for file in self.input_files:
            self.file_listbox.insert(tk.END, os.path.basename(file))

    def preview_files(self):
        """Preview selected files"""
        if not self.input_files:
            messagebox.showwarning("No Files", "Please select files first.")
            return

        # Show preview of first file
        file_path = self.input_files[0]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:20]  # Read first 20 lines

            preview_window = tk.Toplevel(self.master)
            preview_window.title(f"Preview - {os.path.basename(file_path)}")
            preview_window.geometry("800x600")

            text = tk.Text(preview_window, wrap=tk.NONE)
            text.pack(fill=tk.BOTH, expand=True)

            # Add scrollbars
            yscroll = ttk.Scrollbar(text, command=text.yview)
            xscroll = ttk.Scrollbar(preview_window, command=text.xview, orient=tk.HORIZONTAL)
            text.config(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
            yscroll.pack(side=tk.RIGHT, fill=tk.Y)
            xscroll.pack(side=tk.BOTTOM, fill=tk.X)

            for line in lines:
                text.insert(tk.END, line)

            # Identify header line if auto mode
            if self.header_detection.get() == "auto":
                header_line = next((i for i, line in enumerate(lines) if ',' in line), -1)
                if header_line >= 0:
                    text.tag_configure("header", background="yellow")
                    text.tag_add("header", f"{header_line + 1}.0", f"{header_line + 1}.end")

                    if self.skip_units.get() and header_line + 1 < len(lines):
                        text.tag_configure("units", background="lightblue")
                        text.tag_add("units", f"{header_line + 2}.0", f"{header_line + 2}.end")

                    status_text = f"Auto-detected header at line {header_line + 1}"
                    ttk.Label(preview_window, text=status_text).pack(pady=5)

        except Exception as e:
            messagebox.showerror("Error", f"Error previewing file: {str(e)}")

    def load_files(self):
        """Load all selected files and prepare for processing"""
        if not self.input_files:
            messagebox.showwarning("No Files", "Please select files first.")
            return

        self.processed_dfs = {}
        self.sensor_depths = {}

        success_count = 0

        for file_path in self.input_files:
            try:
                # Determine header row
                if self.header_detection.get() == "auto":
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    header_line = next((i for i, line in enumerate(lines) if ',' in line), 0)
                else:
                    header_line = self.skip_lines.get()

                # Skip units row if applicable
                skiprows = header_line
                if self.skip_units.get():
                    skiprows = [header_line + 1]  # Skip the units row, keep header

                # Read the file
                df = pd.read_csv(file_path, skiprows=skiprows, skipinitialspace=True, dtype=str, encoding='utf-8')

                # Clean column names
                df.columns = df.columns.str.strip()

                # Extract sensor depth
                if self.depth_extraction.get() == "filename":
                    basename = os.path.basename(file_path)
                    pattern = self.filename_pattern.get()
                    try:
                        match = re.search(pattern, basename)
                        if match:
                            depth = float(match.group(1))
                        else:
                            depth = float(self.input_files.index(file_path))
                            messagebox.showwarning("Depth Extraction",
                                                   f"Could not extract depth from filename {basename}. Using index as depth.")
                    except Exception as e:
                        depth = float(self.input_files.index(file_path))
                        messagebox.showwarning("Depth Extraction Error",
                                               f"Error extracting depth from {basename}: {str(e)}. Using index as depth.")
                else:  # Manual entry
                    depth = simpledialog.askfloat("Enter Depth",
                                                  f"Enter depth (meters) for {os.path.basename(file_path)}:",
                                                  parent=self.master)
                    if depth is None:  # User cancelled
                        depth = float(self.input_files.index(file_path))

                # Store results
                self.processed_dfs[file_path] = df
                self.sensor_depths[file_path] = depth
                success_count += 1

            except Exception as e:
                messagebox.showerror("Error", f"Error loading file {os.path.basename(file_path)}: {str(e)}")

        if success_count > 0:
            self.status_var.set(f"Successfully loaded {success_count} of {len(self.input_files)} files")

            # Update available variables in the processing tab
            if self.processed_dfs:
                # Get columns from the first dataframe
                first_df = next(iter(self.processed_dfs.values()))
                self.update_available_variables(first_df.columns)

            # Move to the next tab
            self.notebook.select(1)  # Select processing tab
        else:
            self.status_var.set("Failed to load any files")

    def update_available_variables(self, columns):
        """Update the available variables listbox"""
        self.available_vars.delete(0, tk.END)
        for col in columns:
            self.available_vars.insert(tk.END, col)

    def add_variables(self):
        """Add selected variables to process"""
        selected = [self.available_vars.get(i) for i in self.available_vars.curselection()]
        for var in selected:
            if var not in self.selected_vars.get(0, tk.END):
                self.selected_vars.insert(tk.END, var)

        # Update rename entries
        self.update_rename_entries()

    def remove_variables(self):
        """Remove selected variables from processing"""
        selected = [self.selected_vars.get(i) for i in self.selected_vars.curselection()]
        for var in selected:
            items = self.selected_vars.get(0, tk.END)
            index = items.index(var)
            self.selected_vars.delete(index)

        # Update rename entries
        self.update_rename_entries()

    def update_rename_entries(self):
        """Update rename entries based on selected variables"""
        # Clear existing entries
        for widget in self.rename_container.winfo_children():
            widget.destroy()

        # Create new entries
        self.rename_vars = {}
        row = 0
        for var in self.selected_vars.get(0, tk.END):
            ttk.Label(self.rename_container, text=var).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            rename_var = tk.StringVar(value=var)
            self.rename_vars[var] = rename_var
            ttk.Entry(self.rename_container, textvariable=rename_var, width=20).grid(row=row, column=1, sticky=tk.W,
                                                                                     padx=5, pady=2)
            row += 1

    def process_data(self):
        """Process the data according to user settings"""
        if not self.processed_dfs:
            messagebox.showwarning("No Data", "Please load files first.")
            return

        selected_vars = list(self.selected_vars.get(0, tk.END))
        if not selected_vars:
            messagebox.showwarning("No Variables", "Please select variables to process.")
            return

        try:
            # Process each file
            self.depth_arrays = {}

            for file_path, df in self.processed_dfs.items():
                # Select and rename columns
                selected_cols = {}
                for var in selected_vars:
                    if var in df.columns:
                        new_name = self.rename_vars[var].get()
                        selected_cols[var] = new_name

                processed_df = df[selected_cols.keys()].rename(columns=selected_cols)

                # Convert data types
                numeric_cols = [col.strip() for col in self.numeric_cols.get().split(',') if col.strip()]
                for col in numeric_cols:
                    if col in processed_df.columns:
                        processed_df[col] = pd.to_numeric(processed_df[col].str.replace(',', ''), errors='coerce')

                datetime_cols = [col.strip() for col in self.datetime_cols.get().split(',') if col.strip()]
                # In the process_data function where you convert datetime columns
                for col in datetime_cols:
                    if col in processed_df.columns:
                        # Add error handling and format specification
                        try:
                            processed_df[col] = pd.to_datetime(processed_df[col], errors='coerce', format=None)
                            # Check if conversion was successful
                            if processed_df[col].isna().all():
                                print(f"Warning: Failed to convert {col} to datetime. Trying alternate formats...")
                                # Try common date formats explicitly
                                for fmt in ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%d-%b-%Y %H:%M:%S']:
                                    try:
                                        processed_df[col] = pd.to_datetime(processed_df[col], errors='coerce',
                                                                           format=fmt)
                                        if not processed_df[col].isna().all():
                                            print(f"Successfully converted using format: {fmt}")
                                            break
                                    except:
                                        continue
                        except Exception as e:
                            print(f"Error in datetime conversion for {col}: {e}")

                # Set time index if specified
                time_col = self.time_index.get()
                if time_col in processed_df.columns:
                    processed_df.set_index(time_col, inplace=True)

                # Resample if requested
                resample_freq = self.resample_freq.get()
                if resample_freq != "None" and not processed_df.index.empty and isinstance(processed_df.index,
                                                                                           pd.DatetimeIndex):
                    method = self.resample_method.get()
                    if method == "mean":
                        processed_df = processed_df.resample(resample_freq).mean()
                    elif method == "median":
                        processed_df = processed_df.resample(resample_freq).median()
                    elif method == "max":
                        processed_df = processed_df.resample(resample_freq).max()
                    elif method == "min":
                        processed_df = processed_df.resample(resample_freq).min()
                    elif method == "first":
                        processed_df = processed_df.resample(resample_freq).first()
                    elif method == "last":
                        processed_df = processed_df.resample(resample_freq).last()

                # Store the processed dataframe by depth
                depth = self.sensor_depths[file_path]
                self.depth_arrays[depth] = processed_df

            # Update interpolation variables based on columns
            if self.depth_arrays:
                sample_df = next(iter(self.depth_arrays.values()))
                self.update_interpolation_variables(sample_df.columns)

            self.status_var.set(f"Processed {len(self.depth_arrays)} time series")

            # Move to interpolation tab
            self.notebook.select(2)

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Processing Error", f"Error during data processing: {str(e)}")

    def update_interpolation_variables(self, columns):
        """Update interpolation variable checkboxes"""
        # Clear existing entries
        for widget in self.interp_vars_container.winfo_children():
            widget.destroy()

        # Create new checkboxes
        self.interp_var_checkboxes = {}
        row, col = 0, 0
        for var_name in columns:
            var = tk.BooleanVar(value=True)
            self.interp_var_checkboxes[var_name] = var
            cb = ttk.Checkbutton(self.interp_vars_container, text=var_name, variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            col += 1
            if col > 2:  # 3 columns of checkboxes
                col = 0
                row += 1

    def preview_depths(self):
        """Preview the sensor depths that will be used for interpolation"""
        if not self.depth_arrays:
            messagebox.showwarning("No Data", "Please process data first.")
            return

        depths = sorted(self.depth_arrays.keys())

        # Create preview window
        preview_window = tk.Toplevel(self.master)
        preview_window.title("Sensor Depth Preview")
        preview_window.geometry("400x500")

        # Display depths
        ttk.Label(preview_window, text="Detected Sensor Depths:").pack(anchor=tk.W, padx=10, pady=5)

        list_frame = ttk.Frame(preview_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        depth_list = tk.Listbox(list_frame, height=15, width=30, yscrollcommand=scrollbar.set)
        depth_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=depth_list.yview)

        for depth in depths:
            depth_list.insert(tk.END, f"{depth:.2f} m")

        # Display sample data
        if depths:
            ttk.Label(preview_window, text=f"Sample data for depth {depths[0]:.2f} m:").pack(anchor=tk.W, padx=10,
                                                                                             pady=5)

            sample_frame = ttk.Frame(preview_window)
            sample_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            y_scroll = ttk.Scrollbar(sample_frame)
            y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            x_scroll = ttk.Scrollbar(sample_frame, orient=tk.HORIZONTAL)
            x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

            sample_text = tk.Text(sample_frame, wrap=tk.NONE, height=10)
            sample_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            sample_text.config(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
            y_scroll.config(command=sample_text.yview)
            x_scroll.config(command=sample_text.xview)

            # Display sample data
            sample_df = self.depth_arrays[depths[0]]
            sample_text.insert(tk.END, str(sample_df.head()))

    def edit_sensor_depths(self):
        """Edit the sensor depths manually"""
        if not self.depth_arrays:
            messagebox.showwarning("No Data", "Please process data first.")
            return

        # Create edit window
        edit_window = tk.Toplevel(self.master)
        edit_window.title("Edit Sensor Depths")
        edit_window.geometry("400x500")

        # Create a frame for the depth entries
        entries_frame = ttk.Frame(edit_window)
        entries_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Display current depths with edit fields
        depth_entries = {}
        row = 0

        ttk.Label(entries_frame, text="Sensor", width=10).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(entries_frame, text="Depth (m)", width=10).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1

        for i, (depth, df) in enumerate(sorted(self.depth_arrays.items())):
            ttk.Label(entries_frame, text=f"Sensor {i + 1}").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            depth_var = tk.DoubleVar(value=depth)
            depth_entries[depth] = depth_var
            ttk.Entry(entries_frame, textvariable=depth_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=5,
                                                                            pady=5)
            row += 1

        # Save button
        def save_depths():
            new_depth_arrays = {}
            for old_depth, depth_var in depth_entries.items():
                new_depth = depth_var.get()
                new_depth_arrays[new_depth] = self.depth_arrays[old_depth]

            self.depth_arrays = new_depth_arrays
            messagebox.showinfo("Success", "Sensor depths updated successfully.")
            edit_window.destroy()

        ttk.Button(edit_window, text="Save Changes", command=save_depths).pack(pady=10)

    def perform_interpolation(self):
        """Perform interpolation on the processed data"""
        if not self.depth_arrays:
            messagebox.showwarning("No Data", "Please process data first.")
            return

        try:
            # Get interpolation settings
            depth_res = self.depth_resolution.get()
            max_depth = self.max_depth.get()
            fill_values = self.fill_values.get()

            # Get variables to interpolate
            variables_to_interpolate = []
            for var, checkbox in self.interp_var_checkboxes.items():
                if checkbox.get():
                    variables_to_interpolate.append(var)

            if not variables_to_interpolate:
                messagebox.showwarning("No Variables", "Please select at least one variable to interpolate.")
                return

            # Organize data by variable and interpolate
            self.interpolated_arrays = {}

            # Get unique time index
            time_indices = []
            for df in self.depth_arrays.values():
                time_indices.append(df.index)

            # Get common time index or use the first one if they differ
            if time_indices:
                # Check if all time indices are the same
                if all(idx.equals(time_indices[0]) for idx in time_indices):
                    time_index = time_indices[0]
                else:
                    # Use intersection if they differ
                    time_index = time_indices[0]
                    for idx in time_indices[1:]:
                        time_index = time_index.intersection(idx)

                    if len(time_index) == 0:
                        messagebox.showwarning("No Common Times",
                                               "No common time points found across sensors. Using first sensor's time index.")
                        time_index = time_indices[0]
            else:
                messagebox.showerror("No Time Index", "Could not extract time index from data.")
                return

            # Create depth points for interpolation
            depth_points = np.arange(0, max_depth + depth_res, depth_res)

            # Get the sensor depths and organize the data
            sensor_depths = sorted(self.depth_arrays.keys())

            # Perform interpolation for each variable
            for var in variables_to_interpolate:
                # Create 2D array for variable
                var_array = np.empty((len(depth_points), len(time_index)))
                var_array.fill(np.nan)

                # Extract data for this variable from each sensor
                var_data = {}
                for depth, df in self.depth_arrays.items():
                    if var in df.columns:
                        # Align to the common time index
                        if all(idx in df.index for idx in time_index):
                            var_data[depth] = df.loc[time_index, var].values
                        else:
                            # Reindex to match the common time index
                            reindexed = df.reindex(time_index)
                            var_data[depth] = reindexed[var].values

                if not var_data:
                    messagebox.showwarning("Missing Variable",
                                           f"Variable '{var}' not found in any sensor data. Skipping.")
                    continue

                # Interpolate for each time point
                for t_idx in range(len(time_index)):
                    # Get values at this time point across depths
                    depths = []
                    values = []
                    for depth, data in var_data.items():
                        if t_idx < len(data) and not np.isnan(data[t_idx]):
                            depths.append(depth)
                            values.append(data[t_idx])

                    if len(depths) >= 2:  # Need at least 2 points for interpolation
                        # Interpolate
                        depth_sorted_indices = np.argsort(depths)
                        depths_sorted = np.array(depths)[depth_sorted_indices]
                        values_sorted = np.array(values)[depth_sorted_indices]

                        for d_idx, depth in enumerate(depth_points):
                            # If depth is within sensor range, interpolate
                            if depths_sorted[0] <= depth <= depths_sorted[-1]:
                                # Find bracketing sensors
                                idx_above = np.searchsorted(depths_sorted, depth)
                                if idx_above == 0:
                                    # At or below the shallowest sensor
                                    var_array[d_idx, t_idx] = values_sorted[0]
                                elif idx_above == len(depths_sorted):
                                    # At or above the deepest sensor
                                    var_array[d_idx, t_idx] = values_sorted[-1]
                                elif depth == depths_sorted[idx_above]:
                                    # Exactly at a sensor depth
                                    var_array[d_idx, t_idx] = values_sorted[idx_above]
                                else:
                                    # Interpolate between sensors
                                    idx_below = idx_above - 1
                                    d_above = depths_sorted[idx_above]
                                    d_below = depths_sorted[idx_below]
                                    v_above = values_sorted[idx_above]
                                    v_below = values_sorted[idx_below]

                                    # Linear interpolation
                                    weight_above = (depth - d_below) / (d_above - d_below)
                                    weight_below = 1 - weight_above
                                    var_array[d_idx, t_idx] = weight_below * v_below + weight_above * v_above
                    elif len(depths) == 1:
                        # Only one valid sensor at this time point, use its value for all depths
                        var_array[:, t_idx] = values[0]

                # Fill values above/below if requested
                if fill_values and depths:
                    # For each time point
                    for t_idx in range(len(time_index)):
                        valid_depth_indices = np.where(~np.isnan(var_array[:, t_idx]))[0]
                        if len(valid_depth_indices) > 0:
                            # Fill above shallowest sensor
                            min_valid_idx = valid_depth_indices[0]
                            top_value = var_array[min_valid_idx, t_idx]
                            var_array[:min_valid_idx, t_idx] = top_value

                            # Fill below deepest sensor
                            max_valid_idx = valid_depth_indices[-1]
                            bottom_value = var_array[max_valid_idx, t_idx]
                            var_array[max_valid_idx + 1:, t_idx] = bottom_value
                # Make sure the time index is properly saved as datetime
                self.interpolated_arrays[var] = {
                    'data': var_array,
                    'depths': depth_points,
                    'times': pd.DatetimeIndex(time_index)  # Ensure it's a DatetimeIndex
                }
                # Store the interpolated array
                #self.interpolated_arrays[var] = {
                    #'data': var_array,
                    #'depths': depth_points,
                    #'times': time_index
                #}

            # Update visualization variables
            self.update_visualization_variables()

            self.status_var.set(f"Interpolated {len(variables_to_interpolate)} variables")

            # Move to visualization tab
            self.notebook.select(3)

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Interpolation Error", f"Error during interpolation: {str(e)}")

    def update_visualization_variables(self):
        """Update the visualization variable dropdown"""
        if not self.interpolated_arrays:
            return

        variables = list(self.interpolated_arrays.keys())
        self.viz_var_combo['values'] = variables

        if variables:
            self.viz_variable.set(variables[0])

            # Update plot title based on selected variable
            self.plot_title.set(f"{variables[0]} Contour Plot")

    def generate_plot(self):
        """Generate visualization of interpolated data"""
        if not self.interpolated_arrays:
            messagebox.showwarning("No Data", "Please perform interpolation first.")
            return

        variable = self.viz_variable.get()
        if not variable or variable not in self.interpolated_arrays:
            messagebox.showwarning("Invalid Variable", "Please select a valid variable to visualize.")
            return

        try:
            # Get plot settings
            title = self.plot_title.get()
            x_label = self.x_label.get()
            y_label = self.y_label.get()
            cmap = self.colormap.get()
            fig_width = self.fig_width.get()
            fig_height = self.fig_height.get()
            font_size = self.font_size.get()
            font_family = self.font_family.get()
            invert_y = self.invert_y.get()
            time_format = self.time_format.get()
            num_ticks = self.num_ticks.get()

            # Get data
            var_data = self.interpolated_arrays[variable]['data']
            depths = self.interpolated_arrays[variable]['depths']
            times = self.interpolated_arrays[variable]['times']

            # Debug info
            print(f"Data shape: {var_data.shape}")
            print(f"Depths shape: {depths.shape}")
            print(f"Times shape: {len(times)}")
            print(f"Data contains NaN: {np.isnan(var_data).any()}")
            print(f"Time index type: {type(times)}")
            print(f"First 5 time values: {times[:5]}")

            # Handle NaN values in the data array
            # (Your existing NaN handling code here)

            # Create figure
            plt.close('all')
            plt.figure(figsize=(fig_width, fig_height))

            # Set font properties
            plt.rcParams.update({
                'font.family': font_family,
                'font.size': font_size
            })

            # Create normalization
            if self.normalization.get() == "manual":
                norm = Normalize(vmin=self.norm_min.get(), vmax=self.norm_max.get())
            else:
                norm = None

            # Check if times is a DatetimeIndex
            if isinstance(times, pd.DatetimeIndex) or pd.api.types.is_datetime64_any_dtype(times):
                # Convert to matplotlib dates for imshow
                time_nums = mdates.date2num(times)
                extent = [time_nums.min(), time_nums.max(), depths.max(), depths.min()]

                # Create the plot
                im = plt.imshow(var_data, aspect='auto', origin='upper',
                                extent=extent, cmap=cmap, norm=norm, interpolation='nearest')

                # Format x-axis with dates
                ax = plt.gca()
                ax.xaxis_date()

                # Set up ticks with explicit date formatter
                tick_locations = np.linspace(time_nums.min(), time_nums.max(), num_ticks)
                ax.set_xticks(tick_locations)

                # Format tick labels
                date_formatter = mdates.DateFormatter(time_format)
                ax.xaxis.set_major_formatter(date_formatter)
                plt.xticks(rotation=45, ha='right')

                # Ensure the formatter is actually applied
                ax.xaxis.set_tick_params(rotation=45)
                plt.gcf().autofmt_xdate()

            else:
                # Alternative approach if time index is not recognized as datetime
                print("Warning: Time index is not recognized as DatetimeIndex. Attempting conversion...")
                try:
                    # Try to convert times to datetime if it's not already
                    if isinstance(times, (list, np.ndarray, pd.Series)):
                        times_dt = pd.to_datetime(times)
                        time_nums = mdates.date2num(times_dt)
                        extent = [time_nums.min(), time_nums.max(), depths.max(), depths.min()]

                        # Create the plot
                        im = plt.imshow(var_data, aspect='auto', origin='upper',
                                        extent=extent, cmap=cmap, norm=norm, interpolation='nearest')

                        # Format x-axis with dates
                        ax = plt.gca()
                        ax.xaxis_date()

                        # Set up ticks
                        tick_locations = np.linspace(time_nums.min(), time_nums.max(), num_ticks)
                        ax.set_xticks(tick_locations)

                        # Format tick labels
                        date_formatter = mdates.DateFormatter(time_format)
                        ax.xaxis.set_major_formatter(date_formatter)
                        plt.xticks(rotation=45, ha='right')
                        plt.gcf().autofmt_xdate()
                    else:
                        # Fallback to numeric index
                        im = plt.imshow(var_data, aspect='auto', origin='upper',
                                        extent=[0, len(times) - 1, depths.max(), depths.min()],
                                        cmap=cmap, norm=norm, interpolation='nearest')

                        # Set up ticks
                        tick_locations = np.linspace(0, len(times) - 1, num_ticks)
                        tick_labels = [str(times[int(tick)]) if 0 <= tick < len(times) else ''
                                       for tick in tick_locations]
                        plt.xticks(tick_locations, tick_labels, rotation=45, ha='right')
                except Exception as e:
                    print(f"Failed to convert time index: {e}")
                    # Fallback to numeric index
                    im = plt.imshow(var_data, aspect='auto', origin='upper',
                                    extent=[0, len(times) - 1, depths.max(), depths.min()],
                                    cmap=cmap, norm=norm, interpolation='nearest')

                    # Set up ticks
                    tick_locations = np.linspace(0, len(times) - 1, num_ticks)
                    tick_labels = [str(times[int(tick)]) if 0 <= tick < len(times) else ''
                                   for tick in tick_locations]
                    plt.xticks(tick_locations, tick_labels, rotation=45, ha='right')

            # Add colorbar
            cbar = plt.colorbar(im)
            cbar.set_label(variable)

            # Set labels and title
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.title(title)

            # Invert y-axis if requested
            if not invert_y:  # Since imshow with origin='upper' already inverts it
                plt.gca().invert_yaxis()

            # Ensure proper layout
            plt.tight_layout()
            plt.show()

            # Store the current figure for saving
            self.current_figure = plt.gcf()

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Visualization Error", f"Error during plot generation: {str(e)}")

    def save_plot(self):
        """Save the current plot to a file"""
        if not hasattr(self, 'current_figure') or self.current_figure is None:
            messagebox.showwarning("No Plot", "Please generate a plot first.")
            return

        # Get file format
        fmt = self.save_format.get().lower()
        dpi = self.save_dpi.get()

        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}",
            filetypes=[(f"{fmt.upper()} files", f"*.{fmt}"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.current_figure.savefig(file_path, format=fmt, dpi=dpi, bbox_inches='tight')
                self.status_var.set(f"Plot saved to {file_path}")
                messagebox.showinfo("Save Successful", f"Plot saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Error saving plot: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SensorDataProcessor(root)
    root.mainloop()