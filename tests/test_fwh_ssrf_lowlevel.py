
import unittest
from unittest.mock import patch, MagicMock
import soniclit.fwh_solver as fwh

class TestFWHLowLevelSSRF(unittest.TestCase):

    @patch('soniclit.fwh_solver.pd.read_csv')
    def test_calculate_source_terms_serial_ssrf(self, mock_read_csv):
        # Mock inputs
        surf_file = "http://attacker.com/data.csv"
        # minimal mock for preprocessed_data to avoid unrelated errors if it gets that far
        preprocessed_data = {'n': MagicMock(), 'r': MagicMock()}

        # We assert that it raises the specific ValueError and read_csv is not called.
        with self.assertRaises(ValueError) as cm:
             fwh.calculate_source_terms_serial(
                surf_file, preprocessed_data,
                ambient_pressure=101325, ambient_density=1.225,
                speed_of_sound=340, mach_number=[0,0,0],
                f=0, is_permeable=False
            )

        self.assertIn("Security: Remote file paths are not allowed.", str(cm.exception))
        mock_read_csv.assert_not_called()

    @patch('soniclit.fwh_solver.pd.read_csv')
    @patch('soniclit.fwh_solver.MPI_AVAILABLE', True) # Mock MPI as available to reach the code
    @patch('soniclit.fwh_solver.comm') # Mock communicator
    def test_calculate_source_terms_parallel_ssrf(self, mock_comm, mock_read_csv):
        # Mock inputs
        surf_file = "http://attacker.com/data.csv"
        preprocessed_data = MagicMock() # Mock array/df

        # Same logic: expect Security ValueError and no read_csv call.
        with self.assertRaises(ValueError) as cm:
             fwh.calculate_source_terms_parallel(
                surf_file, preprocessed_data,
                ambient_pressure=101325, ambient_density=1.225,
                speed_of_sound=340, mach_number=[0,0,0],
                f=0, is_permeable=False
            )

        self.assertIn("Security: Remote file paths are not allowed.", str(cm.exception))
        mock_read_csv.assert_not_called()

    @patch('soniclit.fwh_solver.pd.read_csv')
    def test_calculate_source_terms_serial_pathlib(self, mock_read_csv):
        # Test regression: pathlib.Path should not crash with TypeError
        # It should pass security check (no "://") and proceed to call read_csv (mocked)
        from pathlib import Path
        surf_file = Path("local_data.csv")
        preprocessed_data = {'n': MagicMock(), 'r': MagicMock()}

        # We expect read_csv to be called (or other error if mock return value is bad)
        # But NOT TypeError or Security ValueError
        try:
             fwh.calculate_source_terms_serial(
                surf_file, preprocessed_data,
                ambient_pressure=101325, ambient_density=1.225,
                speed_of_sound=340, mach_number=[0,0,0],
                f=0, is_permeable=False
            )
        except Exception:
            # We don't care if it fails later due to mock data
            pass

        # Verify read_csv WAS called with the Path object
        mock_read_csv.assert_called()

if __name__ == '__main__':
    unittest.main()
