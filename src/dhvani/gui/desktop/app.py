import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
import os
import ast

# Import Dhvani modules
import dhvani.fwh as fwh
import dhvani.spectral_analysis as sa

class DhvaniApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dhvani GUI")
        self.root.geometry("800x700")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.fwh_tab = ttk.Frame(self.notebook)
        self.spectral_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.fwh_tab, text="FWH Solver")
        self.notebook.add(self.spectral_tab, text="Spectral Analysis")

        self.setup_fwh_tab()
        self.setup_spectral_tab()

    def setup_fwh_tab(self):
        frame = self.fwh_tab

        # Grid layout
        row = 0

        # Surface File
        ttk.Label(frame, text="Surface File Prefix:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.fwh_surf_file = ttk.Entry(frame, width=50)
        self.fwh_surf_file.grid(row=row, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_surf_file).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        # Output File
        ttk.Label(frame, text="Output File Prefix:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.fwh_out_file = ttk.Entry(frame, width=50)
        self.fwh_out_file.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        # Observer Locations
        ttk.Label(frame, text="Observer Locations (e.g. [[0,0,10]]):").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.fwh_obs_loc = ttk.Entry(frame, width=50)
        self.fwh_obs_loc.insert(0, "[[0.0, 0.0, 1.0]]")
        self.fwh_obs_loc.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        # Time setup
        ttk.Label(frame, text="Time Step (dt):").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.fwh_dt = ttk.Entry(frame, width=20)
        self.fwh_dt.insert(0, "0.01")
        self.fwh_dt.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        ttk.Label(frame, text="Number of Steps:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.fwh_steps = ttk.Entry(frame, width=20)
        self.fwh_steps.insert(0, "10")
        self.fwh_steps.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        # Mach Number
        ttk.Label(frame, text="Mach Number (e.g. [0.1, 0, 0]):").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.fwh_ma = ttk.Entry(frame, width=50)
        self.fwh_ma.insert(0, "[0.0, 0.0, 0.0]")
        self.fwh_ma.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        # Temperature
        ttk.Label(frame, text="Temperature (K):").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.fwh_temp = ttk.Entry(frame, width=20)
        self.fwh_temp.insert(0, "298.0")
        self.fwh_temp.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        # Permeable
        self.fwh_perm_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Permeable Surface", variable=self.fwh_perm_var).grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        # Run Button
        self.fwh_run_btn = ttk.Button(frame, text="Run FWH Solver", command=self.run_fwh)
        self.fwh_run_btn.grid(row=row, column=0, columnspan=3, pady=20)
        row += 1

        # Log area
        ttk.Label(frame, text="Logs:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        row += 1
        self.fwh_log = tk.Text(frame, height=10, width=80)
        self.fwh_log.grid(row=row, column=0, columnspan=3, padx=5, pady=5)

    def setup_spectral_tab(self):
        frame = self.spectral_tab

        row = 0
        # Signal File
        ttk.Label(frame, text="Signal CSV File:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.sa_file = ttk.Entry(frame, width=50)
        self.sa_file.grid(row=row, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_sa_file).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        # Columns
        ttk.Label(frame, text="Time Column Name:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.sa_time_col = ttk.Entry(frame, width=20)
        self.sa_time_col.insert(0, "Time")
        self.sa_time_col.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        ttk.Label(frame, text="Signal Column Name:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.sa_sig_col = ttk.Entry(frame, width=20)
        self.sa_sig_col.insert(0, "Signal")
        self.sa_sig_col.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        # Method
        ttk.Label(frame, text="Method:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.sa_method = ttk.Combobox(frame, values=["FFT", "Welch"])
        self.sa_method.current(0)
        self.sa_method.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        # Plot Button
        self.sa_plot_btn = ttk.Button(frame, text="Plot Spectrum", command=self.plot_spectrum)
        self.sa_plot_btn.grid(row=row, column=0, columnspan=3, pady=20)
        row += 1

        # Canvas
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=frame)
        self.canvas.get_tk_widget().grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')

    def browse_surf_file(self):
        # Allow selecting "Avg.csv" or "0.csv" and strip suffix?
        # Better: Select directory or just type it.
        # Let's let user select any file and we take the dir + prefix?
        # Actually user needs to select "prefix".
        # Let's ask for "0.csv" and we strip "0.csv"
        filename = filedialog.askopenfilename(title="Select 0.csv file")
        if filename:
            if filename.endswith("0.csv"):
                prefix = filename[:-5]
                self.fwh_surf_file.delete(0, tk.END)
                self.fwh_surf_file.insert(0, prefix)
            else:
                messagebox.showwarning("Warning", "Please select the '0.csv' file to infer prefix.")

    def browse_sa_file(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            self.sa_file.delete(0, tk.END)
            self.sa_file.insert(0, filename)

    def log(self, message):
        self.fwh_log.insert(tk.END, message + "\n")
        self.fwh_log.see(tk.END)

    def run_fwh(self):
        try:
            surf_file = self.fwh_surf_file.get()
            out_file = self.fwh_out_file.get()
            obs_loc = ast.literal_eval(self.fwh_obs_loc.get())
            dt = float(self.fwh_dt.get())
            steps = int(self.fwh_steps.get())
            ma = ast.literal_eval(self.fwh_ma.get())
            perm = self.fwh_perm_var.get()
            temp = float(self.fwh_temp.get())

            t_src = [i*dt for i in range(steps)]

            # Ensure output dir exists
            out_dir = os.path.dirname(out_file)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            self.log("Starting FWH Solver...")
            self.log(f"Surface: {surf_file}")
            self.log(f"Output: {out_file}")

            # Check inputs
            if not isinstance(obs_loc, list):
                raise ValueError("Observer location must be a list of lists.")
            if not isinstance(ma, list):
                raise ValueError("Mach number must be a list.")

            # Run
            res = fwh.stationary_serial(surf_file, out_file, obs_loc, t_src, ma, perm, write=True, Ta=temp)

            self.log("Result: " + str(res))
            messagebox.showinfo("Success", "FWH Solver Completed!")

        except Exception as e:
            self.log(f"Error: {e}")
            messagebox.showerror("Error", str(e))
            # raise e # Uncomment for debugging

    def plot_spectrum(self):
        try:
            filename = self.sa_file.get()
            time_col = self.sa_time_col.get()
            sig_col = self.sa_sig_col.get()
            method = self.sa_method.get()

            df = pd.read_csv(filename)
            if time_col not in df.columns or sig_col not in df.columns:
                raise ValueError(f"Columns {time_col} or {sig_col} not found in CSV.")

            time = df[time_col].values
            sig = df[sig_col].values

            self.ax.clear()

            if method == "FFT":
                freq, df_bin, psd = sa.fft_spectrum(time, sig)
                self.ax.loglog(freq, psd)
                self.ax.set_title("FFT Spectrum")
            elif method == "Welch":
                freq, df_bin, psd = sa.welch_spectrum(time, sig)
                self.ax.loglog(freq, psd)
                self.ax.set_title("Welch Spectrum")

            self.ax.set_xlabel("Frequency (Hz)")
            self.ax.set_ylabel("PSD")
            self.ax.grid(True)
            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = DhvaniApp(root)
    root.mainloop()
