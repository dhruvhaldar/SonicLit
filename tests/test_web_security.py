import unittest
import time
from streamlit.testing.v1 import AppTest

class TestWebSecurityDoS(unittest.TestCase):
    def test_obs_loc_dos_length(self):
        """Test that providing a massive string to Observer Locations is handled safely and quickly."""
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        obs_input = None
        for widget in at.text_input:
            if "Observer Locations" in widget.label:
                obs_input = widget
                break

        self.assertIsNotNone(obs_input, "Could not find 'Observer Locations' input.")

        # Create a massive string (>5000 chars)
        # "0," is 2 chars. 3000 * 2 = 6000 chars.
        huge_payload = "[[" + "0,"*3000 + "0]]"

        start_time = time.time()
        at = obs_input.set_value(huge_payload).run(timeout=5)
        duration = time.time() - start_time

        self.assertLess(duration, 2.0, "Execution took too long, likely parsed the input.")

        # Verify error message
        found_length_error = False
        for error in at.error:
            if "Input too long" in error.value:
                found_length_error = True
                break

        current_val = obs_input.value

        if len(current_val) > 5000:
             self.assertTrue(found_length_error, "Input > 5000 chars but 'Input too long' error not shown.")

    def test_ma_dos_length(self):
        """Test that providing a massive string to Mach Number is handled safely and quickly."""
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        ma_input = None
        for widget in at.text_input:
            if "Mach Number" in widget.label:
                ma_input = widget
                break

        self.assertIsNotNone(ma_input, "Could not find 'Mach Number' input.")

        # Huge payload
        huge_payload = "[" + "0,"*3000 + "0]"

        start_time = time.time()
        at = ma_input.set_value(huge_payload).run(timeout=5)
        duration = time.time() - start_time

        self.assertLess(duration, 2.0, "Execution took too long.")

        found_length_error = False
        for error in at.error:
            if "Input too long" in error.value:
                found_length_error = True
                break

        current_val = ma_input.value

        if len(current_val) > 5000:
             self.assertTrue(found_length_error, "Input > 5000 chars but 'Input too long' error not shown.")
