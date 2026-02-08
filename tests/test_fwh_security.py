import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import soniclit.fwh_solver as fwh

class TestFWHSecurity(unittest.TestCase):

    @patch('soniclit.fwh_solver.pd.read_csv')
    @patch('soniclit.fwh_solver.plt.subplots')
    def test_stationary_serial_ssrf_prevention(self, mock_subplots, mock_read_csv):
        # Mocking subplots to avoid figure creation
        mock_subplots.return_value = (MagicMock(), MagicMock())

        # Inputs
        surf_file = "http://attacker.com/data"
        obs_loc = [[0, 0, 10]]
        t_src = [0, 0.1, 0.2]
        ma = [0.1, 0, 0]
        perm = False

        # Expect ValueError due to security check
        with self.assertRaises(ValueError) as cm:
            fwh.stationary_serial(surf_file, "out", obs_loc, t_src, ma, perm, write=False)

        self.assertEqual(str(cm.exception), "Security: Remote file paths are not allowed.")

        # Ensure read_csv was NOT called
        mock_read_csv.assert_not_called()

    @patch('soniclit.fwh_solver.pd.read_csv')
    @patch('soniclit.fwh_solver.plt.subplots')
    def test_stationary_parallel_ssrf_prevention(self, mock_subplots, mock_read_csv):
        # Mock MPI availability if needed, but since we mock read_csv and expect early exit, it might not reach MPI checks if check is first.
        # However, stationary_parallel checks MPI first.
        # If MPI is not available, it raises RuntimeError.
        # We want to test security check.
        # So we should patch MPI_AVAILABLE to True if we want to reach security check?
        # Or place security check BEFORE MPI check?
        # Security check should be very first thing.

        # If I place security check first, then I don't need to worry about MPI.

        # Inputs
        surf_file = "http://attacker.com/data"
        obs_loc = [[0, 0, 10]]
        t_src = [0, 0.1, 0.2]
        ma = [0.1, 0, 0]
        perm = False

        # Expect ValueError
        with self.assertRaises(ValueError) as cm:
            fwh.stationary_parallel(surf_file, "out", obs_loc, t_src, ma, perm, write=False)

        self.assertEqual(str(cm.exception), "Security: Remote file paths are not allowed.")
        mock_read_csv.assert_not_called()

if __name__ == '__main__':
    unittest.main()
