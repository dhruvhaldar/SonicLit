import unittest
from streamlit.testing.v1 import AppTest

class TestWebUX(unittest.TestCase):
    def test_observer_input_mode(self):
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # Find the radio button
        radio = None
        for r in at.radio:
            if "Observer Location Strategy" in r.label:
                radio = r
                break
        self.assertIsNotNone(radio, "Observer Location Strategy radio not found")

        # 1. Verify Default State: "Single Point" selected
        self.assertEqual(radio.value, "Single Point")

        # Verify 3 number inputs exist for Observer (X, Y, Z)
        labels = [ni.label for ni in at.number_input]
        self.assertIn("Observer X (m)", labels)
        self.assertIn("Observer Y (m)", labels)
        self.assertIn("Observer Z (m)", labels)

        # Verify text input "Coordinates List" is NOT present
        text_inputs = [ti.label for ti in at.text_input]
        self.assertNotIn("Coordinates List", text_inputs)

        # 2. Toggle to "Coordinate List"
        radio.set_value("Coordinate List").run(timeout=10)

        # Verify text input IS present
        text_inputs_after = [ti.label for ti in at.text_input]
        self.assertIn("Coordinates List", text_inputs_after)

        # Verify number inputs (X, Y, Z) should be gone
        labels_after = [ni.label for ni in at.number_input]
        self.assertNotIn("Observer X (m)", labels_after)
        self.assertNotIn("Observer Y (m)", labels_after)
        self.assertNotIn("Observer Z (m)", labels_after)

    def test_mach_vector_inputs(self):
        at = AppTest.from_file("src/soniclit/gui/web/app.py")
        at.run(timeout=10)

        # Verify "Mx", "My", "Mz" inputs exist
        labels = [ni.label for ni in at.number_input]
        self.assertIn("Mach X (Mx)", labels)
        self.assertIn("Mach Y (My)", labels)
        self.assertIn("Mach Z (Mz)", labels)

        # Verify old "Mach Number" text input is gone
        text_inputs = [ti.label for ti in at.text_input]
        # The old label was "Mach Number (e.g. [0.1, 0, 0])"
        self.assertFalse(any("Mach Number" in label for label in text_inputs))

if __name__ == "__main__":
    unittest.main()
