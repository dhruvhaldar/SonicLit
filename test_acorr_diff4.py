import numpy as np
import time

size = 10000000
arr1 = np.random.rand(size)
var = np.var(arr1)
half_len = size // 2

start = time.time()
for _ in range(10):
    res1 = arr1 / var // half_len
time1 = time.time() - start

start = time.time()
for _ in range(10):
    res2 = (arr1 * (1.0 / var)) // half_len
time2 = time.time() - start

print(f"arr / var // half_len: {time1:.4f}s")
print(f"(arr * (1.0 / var)) // half_len: {time2:.4f}s")
print(np.allclose(res1, res2, equal_nan=True))
