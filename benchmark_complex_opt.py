
import numpy as np
import timeit

def benchmark():
    N = 100000
    z1 = np.random.rand(N) + 1j * np.random.rand(N)
    z2 = np.random.rand(N) + 1j * np.random.rand(N)

    def method1():
        return np.abs(z1 * np.conjugate(z2))

    def method2():
        return np.abs(z1) * np.abs(z2)

    # Warmup
    method1()
    method2()

    t1 = timeit.timeit(method1, number=100)
    t2 = timeit.timeit(method2, number=100)

    print(f"Method 1 (abs(z1 * conj(z2))): {t1:.6f} s")
    print(f"Method 2 (abs(z1) * abs(z2)): {t2:.6f} s")

    # Correctness check
    res1 = method1()
    res2 = method2()
    assert np.allclose(res1, res2), "Results are not close!"
    print("Results match.")

if __name__ == "__main__":
    benchmark()
