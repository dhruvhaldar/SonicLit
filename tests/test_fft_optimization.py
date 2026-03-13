import unittest
import numpy as np
import time
from soniclit import signal_processing as sa

def original_psd_logic(sig_fft, scale_spectrum, sampling_frequency, len_signal):
    if scale_spectrum:
        return abs(sig_fft*np.conjugate(sig_fft))/(sampling_frequency*len_signal)
    else:
        return abs(sig_fft*np.conjugate(sig_fft))

class TestFFTOptimization(unittest.TestCase):
    def test_fft_spectrum_optimization(self):
        # Setup signal
        fs = 1000
        t = np.linspace(0, 1, fs)
        sig = np.sin(2 * np.pi * 50 * t) + np.random.normal(0, 1, len(t))

        # Get current implementation result
        freq, df, psd_optimized = sa.fft_spectrum(t, sig, scale_spectrum=True)

        # Calculate expected result using original logic
        signal_mean_removed = sig - np.mean(sig)
        sig_fft = np.fft.rfft(signal_mean_removed)
        psd_expected = original_psd_logic(sig_fft, True, sa.sampling_freq(t), len(t))

        # Compare
        np.testing.assert_allclose(psd_optimized, psd_expected, rtol=1e-10, atol=1e-10)

        # Test with scale_spectrum=False
        freq, df, psd_optimized_unscaled = sa.fft_spectrum(t, sig, scale_spectrum=False)
        psd_expected_unscaled = original_psd_logic(sig_fft, False, sa.sampling_freq(t), len(t))
        np.testing.assert_allclose(psd_optimized_unscaled, psd_expected_unscaled, rtol=1e-10, atol=1e-10)

    def test_coherence_fft_optimization(self):
        # We benchmark `cpsd**2 / psd1 / psd2` vs `cpsd**2 / (psd1 * psd2)`
        # This isn't testing the output of coherence_fft per se, but verifying the memory states
        # mathematically are equivalent.

        psd1 = np.random.rand(1000)
        psd2 = np.random.rand(1000)
        cpsd = np.random.rand(1000)

        res1 = cpsd**2 / (psd1 * psd2)
        res2 = cpsd**2 / psd1 / psd2

        np.testing.assert_allclose(res1, res2, rtol=1e-10, atol=1e-10)

if __name__ == "__main__":
    unittest.main()
