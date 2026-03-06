from soniclit.signal_processing import auto_corr
import numpy as np
sig = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
acorr, _ = auto_corr(sig)
print(acorr[0])
