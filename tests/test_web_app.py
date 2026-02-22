import unittest
import os
import shutil
import zipfile
import time
from streamlit.testing.v1 import AppTest
from tests.generate_dummy_data import generate_fwh_data, generate_signal_data

class TestWebApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate data
        cls.test_dir = "tests/web_e2e_data"
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        os.makedirs(cls.test_dir)

        # FWH Data
        cls.surf_prefix = os.path.join(cls.test_dir, "surf_")
        generate_fwh_data(cls.surf_prefix, steps=5)

        # Create ZIP
        cls.surf_zip = os.path.join(cls.test_dir, "surf_data.zip")
        with zipfile.ZipFile(cls.surf_zip, 'w') as zf:
            for f in os.listdir(cls.test_dir):
                if f.startswith("surf_") and f.endswith(".csv"):
                    zf.write(os.path.join(cls.test_dir, f), arcname=f)

        # Signal Data
        cls.signal_file = os.path.join(cls.test_dir, "signal.csv")
        generate_signal_data(cls.signal_file)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_fwh_tab_load(self):
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)
        self.assertFalse(at.exception)
        self.assertEqual(at.title[0].value, "SonicLit: Aeroacoustics & Signal Processing")

    # Note: Simulating file upload in Streamlit AppTest is currently limited/experimental
    # depending on the version. We will test that the app loads and elements exist.

    def test_spectral_tab_interaction(self):
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # Switch tab (tabs are not directly clickable in AppTest usually, we access elements by key or structure)
        # But we can check if elements exist.

        # We can't easily upload a file via AppTest in standard ways without complex mocking.
        # So we verify the initial state.
        self.assertFalse(at.exception)

    def test_dos_prevention_steps_val(self):
        """Test that setting a huge steps value doesn't crash the app or take forever (DoS)."""
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # Find steps input
        steps_input = None
        for widget in at.number_input:
            if "Number of Steps" in widget.label:
                steps_input = widget
                break

        self.assertIsNotNone(steps_input, "Could not find 'Number of Steps' input.")

        # Attempt to set a huge value (10^8)
        # Without backend clamping, this might cause OOM or long execution time if loop executed.
        # (Though loop only executes on Run, we verified setting value is safe).
        start_time = time.time()
        at = steps_input.set_value(100000000).run(timeout=10)
        duration = time.time() - start_time

        self.assertFalse(at.exception)
        # It should be fast because it shouldn't try to allocate anything huge
        self.assertLess(duration, 5.0, "Setting huge value took too long, possible DoS/Resource Exhaustion")

    def test_total_sim_time_display(self):
        """Test that the Total Simulation Time caption appears and is correct."""
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # Find inputs
        dt_input = None
        steps_input = None
        for widget in at.number_input:
            if "Time Step (s)" in widget.label:
                dt_input = widget
            elif "Number of Steps" in widget.label:
                steps_input = widget

        self.assertIsNotNone(dt_input, "Could not find 'Time Step (s)' input")
        self.assertIsNotNone(steps_input, "Could not find 'Number of Steps' input")

        # Set values
        # Note: changing values triggers rerun
        at = dt_input.set_value(0.5).run(timeout=10)

        # Re-find steps input in the updated app state
        steps_input = None
        for widget in at.number_input:
            if "Number of Steps" in widget.label:
                steps_input = widget
                break

        at = steps_input.set_value(100).run(timeout=10)

        # Check for caption
        expected_text = "Total Simulation Time: **50.0000 s**"
        found = False

        # Check captions
        # Note: AppTest.caption returns a list of Caption elements
        all_text = [c.body for c in at.caption]
        # Also check markdown just in case
        all_text += [m.body for m in at.markdown]

        for text in all_text:
            if expected_text in text:
                found = True
                break

        self.assertTrue(found, f"Caption '{expected_text}' not found in app. Found: {all_text}")

if __name__ == '__main__':
    unittest.main()
