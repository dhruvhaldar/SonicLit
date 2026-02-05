import unittest
import tkinter as tk
from tkinter import messagebox
import os
import shutil
from unittest.mock import patch, MagicMock
from src.dhvani_app import DhvaniApp
from tests.generate_dummy_data import generate_fwh_data, generate_signal_data

class TestGuiE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate data
        cls.test_dir = "tests/e2e_data"
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        os.makedirs(cls.test_dir)

        cls.surf_prefix = os.path.join(cls.test_dir, "surf_")
        generate_fwh_data(cls.surf_prefix, steps=10) # Reduced steps

        cls.signal_file = os.path.join(cls.test_dir, "signal.csv")
        generate_signal_data(cls.signal_file)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def setUp(self):
        # Patch messagebox to avoid hanging on popups
        self.patcher_info = patch('tkinter.messagebox.showinfo')
        self.patcher_error = patch('tkinter.messagebox.showerror')
        self.patcher_warning = patch('tkinter.messagebox.showwarning')
        self.mock_showinfo = self.patcher_info.start()
        self.mock_showerror = self.patcher_error.start()
        self.mock_showwarning = self.patcher_warning.start()

        self.root = tk.Tk()
        self.app = DhvaniApp(self.root)
        self.root.update()

    def tearDown(self):
        self.root.destroy()
        self.patcher_info.stop()
        self.patcher_error.stop()
        self.patcher_warning.stop()

    def test_fwh_flow(self):
        # Set inputs
        self.app.fwh_surf_file.delete(0, tk.END)
        self.app.fwh_surf_file.insert(0, self.surf_prefix)

        out_prefix = os.path.join(self.test_dir, "fwh_out")
        self.app.fwh_out_file.delete(0, tk.END)
        self.app.fwh_out_file.insert(0, out_prefix)

        self.app.fwh_steps.delete(0, tk.END)
        self.app.fwh_steps.insert(0, "5") # Just 5 steps

        # Invoke run
        self.app.fwh_run_btn.invoke()
        self.root.update()

        # Check if error occurred
        if self.mock_showerror.called:
            args, _ = self.mock_showerror.call_args
            self.fail(f"FWH Solver failed with error: {args}")

        # Check output
        expected_csv = out_prefix + "0.csv"
        self.assertTrue(os.path.exists(expected_csv), f"FWH output CSV not found at {expected_csv}")

        # Check output content
        import pandas as pd
        df = pd.read_csv(expected_csv)
        self.assertTrue("p'" in df.columns)
        self.assertTrue(len(df) > 0)

        # Check mock call
        self.mock_showinfo.assert_called_with("Success", "FWH Solver Completed!")

    def test_spectral_flow(self):
        self.app.sa_file.delete(0, tk.END)
        self.app.sa_file.insert(0, self.signal_file)

        self.app.sa_plot_btn.invoke()
        self.root.update()

        if self.mock_showerror.called:
            args, _ = self.mock_showerror.call_args
            self.fail(f"Spectral Plot failed with error: {args}")

        # Check if plot updated
        self.assertTrue(len(self.app.ax.lines) > 0, "No lines plotted in spectral analysis")

if __name__ == '__main__':
    unittest.main()
