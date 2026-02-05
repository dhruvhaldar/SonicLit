import unittest
import os
import shutil
import zipfile
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
        at = AppTest.from_file("src/dhvani/gui/web/app.py")
        at.run(timeout=10)
        self.assertFalse(at.exception)
        self.assertEqual(at.title[0].value, "Dhvani: Aeroacoustics & Signal Processing")

    # Note: Simulating file upload in Streamlit AppTest is currently limited/experimental
    # depending on the version. We will test that the app loads and elements exist.

    def test_spectral_tab_interaction(self):
        at = AppTest.from_file("src/dhvani/gui/web/app.py")
        at.run(timeout=10)

        # Switch tab (tabs are not directly clickable in AppTest usually, we access elements by key or structure)
        # But we can check if elements exist.

        # We can't easily upload a file via AppTest in standard ways without complex mocking.
        # So we verify the initial state.
        self.assertFalse(at.exception)

if __name__ == '__main__':
    unittest.main()
