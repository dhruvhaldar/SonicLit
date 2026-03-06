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

print("Before operations:")
print("auto_correlation:", auto_correlation_old)
print("sig_var:", sig_var_old)
print("len(signal_old)//2:", len(signal_old)//2)

print("\nOld expression parts:")
print("acorr / var:", auto_correlation_old / sig_var_old)
print("acorr / var / val:", auto_correlation_old / sig_var_old / (len(signal_old)//2))
print("acorr / var / val (without parenthesis!):", auto_correlation_old / sig_var_old / len(signal_old)//2)

print("\nNew expression:")
print("acorr * inv:", auto_correlation_old * (1.0 / (sig_var_old * (len(signal_old)//2))))
