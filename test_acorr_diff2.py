import numpy as np

sig = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
signal_old = sig - np.mean(sig)

n = len(signal_old)
import scipy.fft as fft
nfft = fft.next_fast_len(2 * n - 1)
sig_fft = np.fft.rfft(signal_old, n=nfft)
auto_correlation_full = np.fft.irfft(np.abs(sig_fft)**2, n=nfft)
auto_correlation_old = auto_correlation_full[:n]
sig_var_old = np.var(signal_old)
auto_correlation_old = auto_correlation_old / sig_var_old / len(signal_old)//2


sig2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
sig2 -= np.mean(sig2)
n2 = len(sig2)
nfft2 = fft.next_fast_len(2 * n2 - 1)
sig_fft2 = np.fft.rfft(sig2, n=nfft2)
auto_correlation_full2 = np.fft.irfft(np.abs(sig_fft2)**2, n=nfft2)
auto_correlation_new = auto_correlation_full2[:n2]
sig_var_new = np.var(sig2)
auto_correlation_new = auto_correlation_new * (1.0 / (sig_var_new * (len(sig2)//2)))

print("Old:", auto_correlation_old)
print("New:", auto_correlation_new)
