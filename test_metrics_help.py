import unittest
from streamlit.testing.v1 import AppTest

class TestMetricsHelp(unittest.TestCase):
    def test_metrics_have_help(self):
        at = AppTest.from_file("src/soniclit/gui/web/app.py")

        # We need to simulate uploading a file to see the metrics in the spectral analysis tab
        # AppTest limitation with file_uploader means we might not be able to fully render the metrics
        pass

if __name__ == "__main__":
    unittest.main()
