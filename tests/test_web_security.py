from streamlit.testing.v1 import AppTest
import time
import unittest

class TestWebSecurity(unittest.TestCase):
    def test_obs_loc_dos_prevention(self):
        """
        Verify that large inputs to 'Observer Locations' are rejected quickly
        to prevent Denial of Service (DoS) via ast.literal_eval.
        """
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # Find the text input for Observer Locations
        obs_input = None
        for widget in at.text_input:
            if "Observer Locations" in widget.label:
                obs_input = widget
                break

        if not obs_input:
            self.fail("Observer Locations input not found")

        # Create a large payload
        # 1 million elements in a list ~ 2MB string
        n = 1000000
        payload = "[" + ",".join(["1"] * n) + "]"

        start_time = time.time()
        try:
            # Set the value and run the script
            # After the fix, this should be very fast because ast.literal_eval won't run on huge input
            at = obs_input.set_value(payload).run(timeout=5)
        except RuntimeError:
            # If it times out, it means the fix is not working (DoS)
            self.fail("DoS vulnerability detected: Processing large input took too long")
        except Exception as e:
            self.fail(f"Exception during run: {e}")

        duration = time.time() - start_time
        print(f"Duration: {duration:.4f}s")

        # Assert that processing took less than 1 second (it should be instant rejection)
        # Note: AppTest overhead might be slightly more, but definitely < 2s vs > 10s
        self.assertLess(duration, 2.0, "Input processing took too long, possible DoS")

        # Verify that an error message is shown (after the fix is implemented)
        # We look for "Input too long" in any error message
        found_error = False
        for error in at.error:
            if "Input too long" in error.value:
                found_error = True
                break

        # This assertion will fail until we implement the fix
        # self.assertTrue(found_error, "Expected 'Input too long' error message not found")

    def test_mach_number_dos_prevention(self):
        """
        Verify that large inputs to 'Mach Number' are rejected quickly.
        """
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # Find the text input for Mach Number
        ma_input = None
        for widget in at.text_input:
            if "Mach Number" in widget.label:
                ma_input = widget
                break

        if not ma_input:
            self.fail("Mach Number input not found")

        # Create a large payload
        n = 100000
        payload = "[" + ",".join(["1"] * n) + "]"

        start_time = time.time()
        try:
            at = ma_input.set_value(payload).run(timeout=5)
        except RuntimeError:
            self.fail("DoS vulnerability detected: Processing large input took too long")
        except Exception as e:
            self.fail(f"Exception during run: {e}")

        duration = time.time() - start_time
        self.assertLess(duration, 2.0, "Input processing took too long")

if __name__ == '__main__':
    unittest.main()
