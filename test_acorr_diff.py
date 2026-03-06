import numpy as np

# Old
sig = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
signal_old = sig - np.mean(sig)

# New
sig2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
sig2 -= np.mean(sig2)

print("Old signal:", signal_old)
print("New signal:", sig2)
