
import numpy as np
import timeit
import pytest
from src.soniclit.fwh_solver import cubic_spline

def cubic_spline_original(interpolation_weight, f0, f1, f2, f3):
    """
    Original implementation of cubic spline interpolation.
    """
    out = -(interpolation_weight*(1-interpolation_weight)*(1+interpolation_weight)/6)*f0 + (interpolation_weight*(1+interpolation_weight)*(2-interpolation_weight)/2)*f1 + ((1-interpolation_weight)*(1+interpolation_weight)*(2-interpolation_weight)/2)*f2 - (interpolation_weight*(1-interpolation_weight)*(2-interpolation_weight)/6)*f3
    return out

def test_cubic_spline_correctness():
    """
    Verify that the optimized implementation produces the same results as the original.
    """
    N = 100000
    w = np.random.rand(N)
    f0 = np.random.rand(N)
    f1 = np.random.rand(N)
    f2 = np.random.rand(N)
    f3 = np.random.rand(N)

    res_orig = cubic_spline_original(w, f0, f1, f2, f3)
    res_opt = cubic_spline(w, f0, f1, f2, f3)

    np.testing.assert_allclose(res_orig, res_opt, rtol=1e-10, atol=1e-10)
    print("Correctness test passed.")

def benchmark_cubic_spline():
    """
    Benchmark the performance of original vs optimized implementation.
    """
    N = 1000000
    w = np.random.rand(N)
    f0 = np.random.rand(N)
    f1 = np.random.rand(N)
    f2 = np.random.rand(N)
    f3 = np.random.rand(N)

    def run_orig():
        return cubic_spline_original(w, f0, f1, f2, f3)

    def run_opt():
        return cubic_spline(w, f0, f1, f2, f3)

    # Warmup
    run_orig()
    run_opt()

    t_orig = timeit.timeit(run_orig, number=20)
    t_opt = timeit.timeit(run_opt, number=20)

    print(f"Original (20 runs): {t_orig:.6f} s")
    print(f"Optimized (20 runs): {t_opt:.6f} s")
    print(f"Speedup: {t_orig/t_opt:.2f}x")

if __name__ == "__main__":
    test_cubic_spline_correctness()
    benchmark_cubic_spline()
