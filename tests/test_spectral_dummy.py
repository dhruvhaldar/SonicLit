import pytest
import os
import pandas as pd
import numpy as np
import tempfile
from soniclit import signal_processing as sa
from tests.generate_dummy_data import generate_signal_data

def test_spectral_analysis_with_dummy_data():
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "test_signal.csv")
        
        # Generate dummy data
        generate_signal_data(filename=csv_path)
        
        # Read the data back
        assert os.path.exists(csv_path)
        df = pd.read_csv(csv_path)
        
        assert not df.empty
        assert 'Time' in df.columns
        assert 'Signal' in df.columns
        
        time = df['Time'].values
        sig = df['Signal'].values
        
        # Test FFT Spectrum
        freq, df_bin, psd = sa.fft_spectrum(time, sig)
        
        assert len(freq) > 0
        assert len(psd) == len(freq)
        assert df_bin > 0
        
        # Test Welch Spectrum
        freq_w, df_bin_w, psd_w = sa.welch_spectrum(time, sig, chunks=4, overlap=0.5)
        
        assert len(freq_w) > 0
        assert len(psd_w) == len(freq_w)
        # Welch typically results in fewer frequency bins than raw FFT
        assert len(freq_w) <= len(freq)

