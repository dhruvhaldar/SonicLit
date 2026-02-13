import unittest
from soniclit.utils import predict_column_roles

class TestUXHelpers(unittest.TestCase):
    def test_predict_column_roles_standard(self):
        # Case 1: Standard Time, Pressure
        cols = ['Time', 'Pressure']
        time_idx, sig_idx = predict_column_roles(cols)
        self.assertEqual(time_idx, 0)
        self.assertEqual(sig_idx, 1)

    def test_predict_column_roles_reversed(self):
        # Case 2: Pressure, Time
        cols = ['Pressure', 'Time']
        time_idx, sig_idx = predict_column_roles(cols)
        self.assertEqual(time_idx, 1)
        self.assertEqual(sig_idx, 0)

    def test_predict_column_roles_short(self):
        # Case 3: t, p
        cols = ['p', 't']
        time_idx, sig_idx = predict_column_roles(cols)
        self.assertEqual(time_idx, 1)
        self.assertEqual(sig_idx, 0)

    def test_predict_column_roles_multiple_candidates(self):
        # Case 4: timestamp, time_sec (prefer "time" or "t" if exact, otherwise first match?)
        # My logic prefers exact match. If no exact match, it takes first partial match.
        cols = ['data', 'timestamp', 'value']
        time_idx, sig_idx = predict_column_roles(cols)
        self.assertEqual(time_idx, 1) # timestamp contains time
        self.assertEqual(sig_idx, 0) # first non-time

    def test_predict_column_roles_exact_over_partial(self):
        # Case 5: 'time_approx', 'time'
        cols = ['time_approx', 'Time']
        time_idx, sig_idx = predict_column_roles(cols)
        self.assertEqual(time_idx, 1) # Exact 'Time' (case insensitive)

    def test_predict_column_roles_no_match(self):
        # Case 6: No obvious time column
        cols = ['A', 'B']
        time_idx, sig_idx = predict_column_roles(cols)
        self.assertEqual(time_idx, 0) # Default to 0
        self.assertEqual(sig_idx, 1) # Default to first non-time (1)

    def test_predict_column_roles_single_column(self):
        cols = ['OnlyOne']
        time_idx, sig_idx = predict_column_roles(cols)
        self.assertEqual(time_idx, 0)
        self.assertEqual(sig_idx, 0)

if __name__ == '__main__':
    unittest.main()
