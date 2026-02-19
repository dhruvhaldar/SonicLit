import unittest
import time
import os
from streamlit.testing.v1 import AppTest

class TestWebSecurityDoS(unittest.TestCase):
    def test_obs_loc_dos_length(self):
        """Test that providing a massive string to Observer Locations is handled safely and quickly."""
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # Fix: Switch to Coordinate List mode
        radio = None
        for r in at.radio:
            if "Observer Location Strategy" in r.label:
                radio = r
                break
        self.assertIsNotNone(radio, "Could not find 'Observer Location Strategy' radio.")
        at = radio.set_value("Coordinate List").run(timeout=10)

        obs_input = None
        for widget in at.text_input:
            if "Coordinates List" in widget.label:
                obs_input = widget
                break

        self.assertIsNotNone(obs_input, "Could not find 'Coordinates List' input.")

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

    def test_is_file_size_valid(self):
        """Test file size validation helper."""
        from soniclit.utils import is_file_size_valid

        class MockFile:
            def __init__(self, size):
                self.size = size

        # 10MB limit
        limit = 10

        # Valid size (9MB)
        valid_file = MockFile(9 * 1024 * 1024)
        self.assertTrue(is_file_size_valid(valid_file, limit), "9MB should be valid for 10MB limit")

        # Boundary (10MB)
        boundary_file = MockFile(10 * 1024 * 1024)
        self.assertTrue(is_file_size_valid(boundary_file, limit), "10MB should be valid for 10MB limit")

        # Invalid size (11MB)
        invalid_file = MockFile(11 * 1024 * 1024)
        self.assertFalse(is_file_size_valid(invalid_file, limit), "11MB should be invalid for 10MB limit")

    def test_sanitize_markdown(self):
        """Test markdown sanitization helper."""
        from soniclit.utils import sanitize_markdown

        # Test HTML escaping
        unsafe_html = "<script>alert(1)</script>"
        safe_html = sanitize_markdown(unsafe_html)
        self.assertNotIn("<script>", safe_html)
        self.assertIn("&lt;script&gt;", safe_html)

        # Test Markdown link breaking
        unsafe_md = "[Click Me](javascript:alert(1))"
        safe_md = sanitize_markdown(unsafe_md)
        self.assertNotIn("[", safe_md)
        self.assertNotIn("]", safe_md)
        self.assertIn("(Click Me)", safe_md)

        # Test mixed
        unsafe_mixed = "[<script>](url)"
        safe_mixed = sanitize_markdown(unsafe_mixed)
        self.assertIn("(&lt;script&gt;)", safe_mixed)
