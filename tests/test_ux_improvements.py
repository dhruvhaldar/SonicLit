from streamlit.testing.v1 import AppTest
import unittest

class TestUXImprovements(unittest.TestCase):
    def test_fwh_empty_state_present(self):
        """Verify that the FWH Solver tab shows a helpful empty state message initially."""
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # The expected message
        expected_msg = "👈 Configure parameters and upload surface data to generate noise predictions."

        # Check if any info block contains this message
        found = False
        # Note: at.info returns a list of info elements. We need to check their value/markdown.
        # Streamlit AppTest API: element.value is the text.
        for info in at.info:
            if expected_msg in info.value:
                found = True
                break

        self.assertTrue(found, "Empty state info message not found in FWH Solver tab.")

if __name__ == '__main__':
    unittest.main()
