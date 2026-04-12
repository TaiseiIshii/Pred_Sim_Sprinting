"""
post_process_results.py
Post-Processing Framework for Pred_Sim_Sprinting Results

This module provides utilities to:
1. Load and parse .mot (motion) files from simulation results
2. Visualize results as time-series plots
3. Export results to CSV format
4. Validate simulation outputs

Date Created: 2026-02-03
Python 3.7+ compatible
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class MotionFileReader:
    """Reader for OpenSim .mot motion files."""
    
    def __init__(self, file_path):
        """
        Initialize motion file reader.
        
        Parameters:
        -----------
        file_path : str
            Path to .mot file
        """
        self.file_path = Path(file_path)
        self.data = None
        self.headers = None
        self.time = None
        
    def read(self):
        """Read .mot file and parse data."""
        try:
            with open(self.file_path, 'r') as f:
                lines = f.readlines()
            
            # Parse header (skip until we find time column)
            header_row = None
            data_start_row = None
            
            for i, line in enumerate(lines):
                if line.strip().startswith('time'):
                    header_row = i
                    data_start_row = i + 1
                    break
            
            if header_row is None:
                raise ValueError("Could not find 'time' column in .mot file")
            
            # Extract headers
            headers_line = lines[header_row].strip()
            self.headers = headers_line.split()
            
            # Extract data
            data_lines = lines[data_start_row:]
            data_array = []
            
            for line in data_lines:
                if line.strip() and not line.startswith('#'):
                    values = [float(x) for x in line.split()]
                    data_array.append(values)
            
            self.data = np.array(data_array)
            self.time = self.data[:, 0]
            
            print(f"[OK] Loaded {self.file_path.name}")
            print(f"     Time range: {self.time[0]:.3f} to {self.time[-1]:.3f} seconds")
            print(f"     Data points: {len(self.time)}")
            print(f"     Columns: {len(self.headers)}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to read {self.file_path}: {str(e)}")
            return False
    
    def to_dataframe(self):
        """Convert to pandas DataFrame."""
        if self.data is None:
            raise ValueError("No data loaded. Call read() first.")
        return pd.DataFrame(self.data, columns=self.headers)
    
    def export_csv(self, output_path=None):
        """Export data to CSV."""
        if self.data is None:
            raise ValueError("No data loaded. Call read() first.")
        
        if output_path is None:
            output_path = self.file_path.with_suffix('.csv')
        
        df = self.to_dataframe()
        df.to_csv(output_path, index=False)
        print(f"[OK] Exported to {output_path}")
        return output_path


def plot_motion_data(motion_file_path, columns_to_plot=None, output_dir=None):
    """
    Plot motion data from .mot file.
    
    Parameters:
    -----------
    motion_file_path : str
        Path to .mot file
    columns_to_plot : list, optional
        Specific columns to plot. If None, plots first 6 data columns.
    output_dir : str, optional
        Directory to save plots. If None, displays interactively.
    """
    reader = MotionFileReader(motion_file_path)
    if not reader.read():
        return False
    
    df = reader.to_dataframe()
    
    # Determine columns to plot
    if columns_to_plot is None:
        # Plot first 6 non-time columns
        columns_to_plot = df.columns[1:7].tolist()
    
    # Create figure
    n_cols = 3
    n_rows = int(np.ceil(len(columns_to_plot) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
    axes = axes.flatten()
    
    for idx, col in enumerate(columns_to_plot):
        if col in df.columns:
            axes[idx].plot(df['time'], df[col], linewidth=1.5)
            axes[idx].set_xlabel('Time (s)')
            axes[idx].set_ylabel(col)
            axes[idx].grid(True, alpha=0.3)
            axes[idx].set_title(f'{col}')
    
    # Hide unused subplots
    for idx in range(len(columns_to_plot), len(axes)):
        axes[idx].set_visible(False)
    
    plt.tight_layout()
    
    # Save or show
    if output_dir is not None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir) / f"{Path(motion_file_path).stem}_plot.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"[OK] Saved plot to {output_file}")
    else:
        plt.show()
    
    return True


def process_results_directory(results_dir, export_csv=True, plot_results=False):
    """
    Process all .mot files in a results directory.
    
    Parameters:
    -----------
    results_dir : str
        Path to Results directory
    export_csv : bool
        Whether to export each .mot file to CSV
    plot_results : bool
        Whether to generate plots
    """
    results_path = Path(results_dir)
    
    if not results_path.exists():
        print(f"[ERROR] Results directory not found: {results_dir}")
        return
    
    mot_files = list(results_path.glob('*.mot'))
    
    if not mot_files:
        print(f"[WARN] No .mot files found in {results_dir}")
        return
    
    print(f"\nFound {len(mot_files)} .mot file(s)\n")
    
    for mot_file in sorted(mot_files):
        print(f"Processing: {mot_file.name}")
        reader = MotionFileReader(mot_file)
        
        if reader.read():
            if export_csv:
                reader.export_csv()
            if plot_results:
                output_dir = results_path / "plots"
                plot_motion_data(mot_file, output_dir=output_dir)
        print()


def main():
    """Main entry point for post-processing."""
    print("="*50)
    print("Pred_Sim_Sprinting Post-Processing Tool")
    print("="*50 + "\n")
    
    # Detect results directory
    script_dir = Path(__file__).parent
    results_dir = script_dir / "Results"
    
    if not results_dir.exists():
        print(f"[ERROR] Results directory not found at {results_dir}")
        print("Please run main_pred_sim_sprinting.m first to generate results.")
        return 1
    
    # Process all results
    print(f"Results directory: {results_dir}\n")
    process_results_directory(results_dir, export_csv=True, plot_results=True)
    
    print("="*50)
    print("Post-processing completed!")
    print("="*50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
