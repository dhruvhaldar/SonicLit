import unittest
from streamlit.testing.v1 import AppTest

class TestWebUX(unittest.TestCase):
    def test_observer_input_mode(self):
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # Find the radio button
        radio = None
        for r in at.radio:
            if "Observer Location" in r.label:
                radio = r
                break
        self.assertIsNotNone(radio, "Observer Location radio not found")

        # 1. Verify Default State: "Single Point" selected
        self.assertEqual(radio.value, "Single Point")

        # Verify 3 number inputs exist for Observer (Observer X, Observer Y, Observer Z)
        labels = [ni.label for ni in at.number_input]
        self.assertIn("Observer X (m)", labels)
        self.assertIn("Observer Y (m)", labels)
        self.assertIn("Observer Z (m)", labels)

        # Verify text area "Coordinates List" is NOT present
        text_areas = [ta.label for ta in at.text_area]
        self.assertNotIn("Coordinates List", text_areas)

        # NEW CHECK: Verify expander is NOT present in Single Point mode
        expanders = [e.label for e in at.expander if "Preview Observer Locations" in e.label]
        self.assertEqual(len(expanders), 0, "Preview expander should not be visible in Single Point mode")

        # 2. Toggle to "Coordinate List"
        radio.set_value("Coordinate List").run(timeout=10)

        # Verify text area IS present
        text_areas_after = [ta.label for ta in at.text_area]
        self.assertIn("Coordinates List", text_areas_after)

        # Verify number inputs (Observer X, Observer Y, Observer Z) should be gone
        labels_after = [ni.label for ni in at.number_input]
        self.assertNotIn("Observer X (m)", labels_after)
        self.assertNotIn("Observer Y (m)", labels_after)
        self.assertNotIn("Observer Z (m)", labels_after)

    def test_mach_vector_inputs(self):
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # Verify "Mx", "My", "Mz" inputs exist
        labels = [ni.label for ni in at.number_input]
        self.assertIn("Mx", labels)
        self.assertIn("My", labels)
        self.assertIn("Mz", labels)

        # Verify old "Mach Number" text input is gone
        text_inputs = [ti.label for ti in at.text_input]
        # The old label was "Mach Number (e.g. [0.1, 0, 0])"
        self.assertFalse(any("Mach Number" in label for label in text_inputs))

    def test_observer_csv_parsing(self):
        """Test that observer coordinates can be entered as CSV/newline separated values."""
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # Switch to "Coordinate List"
        radio = [r for r in at.radio if "Observer Location" in r.label][0]
        radio.set_value("Coordinate List").run(timeout=10)

        # Find the text area
        text_area = [ta for ta in at.text_area if "Coordinates List" in ta.label][0]

        # Input CSV format (mix of commas and newlines)
        csv_input = "0, 0, 1\n0, 10, 10"
        text_area.set_value(csv_input).run(timeout=10)

        # Verify NO error messages about format
        error_messages = [e.value for e in at.error]
        self.assertFalse(any("Invalid format" in msg for msg in error_messages), f"Unexpected error for valid CSV: {error_messages}")

        # Verify caption confirms 2 observers
        captions = [c.body for c in at.caption if "**2** observer(s)" in c.body]
        self.assertTrue(len(captions) > 0, "Caption did not update to reflect 2 observers parsed from CSV")

        # NEW CHECK: Verify expander and dataframe preview exist
        expanders = [e.label for e in at.expander if "Preview Observer Locations" in e.label]
        self.assertTrue(len(expanders) > 0, "Preview expander not found in Coordinate List mode")

        # We can also check if there is a dataframe inside
        self.assertTrue(len(at.dataframe) > 0, "Dataframe preview not found")

if __name__ == "__main__":
    unittest.main()
