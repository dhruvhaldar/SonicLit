import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib
import sys
if 'pytest' not in sys.modules and not sys.argv[0].endswith('pytest'):
    try:
        matplotlib.use('TkAgg')
    except ImportError:
        pass
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import numpy as np
import os
import ast
import threading

# Import SonicLit modules
import soniclit.fwh_solver as fwh
import soniclit.signal_processing as sa

class SonicLitApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SonicLit GUI")
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
        ttk.Button(frame, text="Browse", command=self.browse_out_file).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        # Observer Location
        ttk.Label(frame, text="Observer Location (Ox, Oy, Oz):").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        obs_frame = ttk.Frame(frame)
        obs_frame.grid(row=row, column=1, sticky='w', padx=5, pady=5)

        self.fwh_ox = ttk.Entry(obs_frame, width=10)
        self.fwh_ox.insert(0, "0.0")
        self.fwh_ox.grid(row=0, column=0, padx=(0, 5))

        self.fwh_oy = ttk.Entry(obs_frame, width=10)
        self.fwh_oy.insert(0, "0.0")
        self.fwh_oy.grid(row=0, column=1, padx=(0, 5))

        self.fwh_oz = ttk.Entry(obs_frame, width=10)
        self.fwh_oz.insert(0, "1.0")
        self.fwh_oz.grid(row=0, column=2)
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
        ttk.Label(frame, text="Mach Vector Components (Mx, My, Mz):").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        ma_frame = ttk.Frame(frame)
        ma_frame.grid(row=row, column=1, sticky='w', padx=5, pady=5)

        self.fwh_mx = ttk.Entry(ma_frame, width=10)
        self.fwh_mx.insert(0, "0.0")
        self.fwh_mx.grid(row=0, column=0, padx=(0, 5))

        self.fwh_my = ttk.Entry(ma_frame, width=10)
        self.fwh_my.insert(0, "0.0")
        self.fwh_my.grid(row=0, column=1, padx=(0, 5))

        self.fwh_mz = ttk.Entry(ma_frame, width=10)
        self.fwh_mz.insert(0, "0.0")
        self.fwh_mz.grid(row=0, column=2)
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
        self.fwh_log.insert(tk.END, "👋 Welcome to the FWH Solver.\nConfigure parameters and click 'Run FWH Solver' to see logs here.\n")
        self.fwh_log.config(state=tk.DISABLED)
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

        # UX Enhancement: Add a helpful empty state to the blank canvas
        self.ax.text(0.5, 0.5, "Upload a CSV and click 'Plot Spectrum' to begin",
                     horizontalalignment='center', verticalalignment='center',
                     transform=self.ax.transAxes, color='gray')
        self.ax.set_axis_off()

        self.canvas = FigureCanvasTkAgg(self.figure, master=frame)
        self.canvas.get_tk_widget().grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')
        row += 1

        # Toolbar
        self.toolbar_frame = ttk.Frame(frame)
        self.toolbar_frame.grid(row=row, column=0, columnspan=3, sticky='ew')
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

    def browse_surf_file(self):
        # Allow selecting "Avg.csv" or "0.csv" and strip suffix?
        # Better: Select directory or just type it.
        # Let's let user select any file and we take the dir + prefix?
        # Actually user needs to select "prefix".
        # Let's ask for "0.csv" and we strip "0.csv"
        filename = filedialog.askopenfilename(title="Select 0.csv file", filetypes=[("0.csv Surface Files", "*0.csv"), ("All Files", "*.*")])
        if filename:
            if filename.endswith("0.csv"):
                prefix = filename[:-5]
                self.fwh_surf_file.delete(0, tk.END)
                self.fwh_surf_file.insert(0, prefix)
            else:
                messagebox.showwarning("Warning", "Please select the '0.csv' file to infer prefix.")

    def browse_out_file(self):
        filename = filedialog.askdirectory(title="Select Output Directory")
        if filename:
            current_path = self.fwh_out_file.get()
            prefix = os.path.basename(current_path)
            if not prefix:
                prefix = "fwh_out"
            self.fwh_out_file.delete(0, tk.END)
            self.fwh_out_file.insert(0, os.path.join(filename, prefix))

    def browse_sa_file(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")])
        if filename:
            self.sa_file.delete(0, tk.END)
            self.sa_file.insert(0, filename)

    def log(self, message):
        self.fwh_log.config(state=tk.NORMAL)
        self.fwh_log.insert(tk.END, message + "\n")
        self.fwh_log.see(tk.END)
        self.fwh_log.config(state=tk.DISABLED)

    def run_fwh(self):
        try:
            surf_file = self.fwh_surf_file.get()
            out_file = self.fwh_out_file.get()

            ox = float(self.fwh_ox.get())
            oy = float(self.fwh_oy.get())
            oz = float(self.fwh_oz.get())
            obs_loc = [[ox, oy, oz]]

            dt = float(self.fwh_dt.get())
            steps = int(self.fwh_steps.get())

            mx = float(self.fwh_mx.get())
            my = float(self.fwh_my.get())
            mz = float(self.fwh_mz.get())
            ma = [mx, my, mz]

            perm = self.fwh_perm_var.get()
            temp = float(self.fwh_temp.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.fwh_run_btn.config(state=tk.DISABLED, text="Running...")
        self.root.update()
        threading.Thread(target=self._run_fwh_thread, args=(surf_file, out_file, obs_loc, dt, steps, ma, perm, temp), daemon=True).start()

    def _run_fwh_thread(self, surf_file, out_file, obs_loc, dt, steps, ma, perm, temp):
        try:

            t_src = [i*dt for i in range(steps)]

            # Ensure output dir exists
            out_dir = os.path.dirname(out_file)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            self.root.after(0, self.log, "Starting FWH Solver...")
            self.root.after(0, self.log, f"Surface: {surf_file}")
            self.root.after(0, self.log, f"Output: {out_file}")

            # Check inputs
            if not isinstance(obs_loc, list):
                raise ValueError("Observer location must be a list of lists.")
            if not isinstance(ma, list):
                raise ValueError("Mach number must be a list.")

            # Run
            res = fwh.stationary_serial(surf_file, out_file, obs_loc, t_src, ma, perm, write=True, ambient_temperature=temp)

            self.root.after(0, self.log, "Result: " + str(res))
            self.root.after(0, messagebox.showinfo, "Success", "FWH Solver Completed!")

        except Exception as e:
            self.root.after(0, self.log, f"Error: {e}")
            self.root.after(0, messagebox.showerror, "Error", str(e))
        finally:
            self.root.after(0, lambda: self.fwh_run_btn.config(state=tk.NORMAL, text="Run FWH Solver"))

    def plot_spectrum(self):
        filename = self.sa_file.get()
        time_col = self.sa_time_col.get()
        sig_col = self.sa_sig_col.get()
        method = self.sa_method.get()

        self.sa_plot_btn.config(state=tk.DISABLED, text="Plotting...")
        self.root.update()
        threading.Thread(target=self._plot_spectrum_thread, args=(filename, time_col, sig_col, method), daemon=True).start()

    def _plot_spectrum_thread(self, filename, time_col, sig_col, method):
        try:

            df = pd.read_csv(filename)
            if time_col not in df.columns or sig_col not in df.columns:
                raise ValueError(f"Columns {time_col} or {sig_col} not found in CSV.")

            time = df[time_col].values
            sig = df[sig_col].values

            self.root.after(0, self.ax.clear)
            self.root.after(0, self.ax.set_axis_on)

            if method == "FFT":
                freq, df_bin, psd = sa.fft_spectrum(time, sig)
                self.root.after(0, self.ax.loglog, freq, psd)
                self.root.after(0, self.ax.set_title, "FFT Spectrum")
            elif method == "Welch":
                freq, df_bin, psd = sa.welch_spectrum(time, sig)
                self.root.after(0, self.ax.loglog, freq, psd)
                self.root.after(0, self.ax.set_title, "Welch Spectrum")

            self.root.after(0, self.ax.set_xlabel, "Frequency (Hz)")
            self.root.after(0, self.ax.set_ylabel, "PSD")
            self.root.after(0, self.ax.grid, True)
            self.root.after(0, self.canvas.draw)

        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", str(e))
        finally:
            self.root.after(0, lambda: self.sa_plot_btn.config(state=tk.NORMAL, text="Plot Spectrum"))

if __name__ == "__main__":
    root = tk.Tk()
    app = SonicLitApp(root)
    root.mainloop()
