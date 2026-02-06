
import numpy as np
import pandas as pd
import timeit

def benchmark_accumulation():
    N_panels = 10000
    p_values = np.random.rand(N_panels)
    p = pd.Series(p_values)

    j_star = np.random.randint(0, 100, size=N_panels)
    j_cond = np.random.randint(0, 2, size=N_panels)

    # Check correctness
    p_act_orig = np.zeros(101)
    n_elm_orig = np.zeros(101)

    p_act_opt = np.zeros(101)
    n_elm_opt = np.zeros(101)

    # Original
    for i in range(len(j_star)):
        p_act_orig[j_star[i]] += p.iloc[i]
        n_elm_orig[j_star[i]] += 1*j_cond[i]

    # Optimized
    np.add.at(p_act_opt, j_star, p.values)
    np.add.at(n_elm_opt, j_star, j_cond)

    assert np.allclose(p_act_orig, p_act_opt), "p_act mismatch"
    assert np.allclose(n_elm_orig, n_elm_opt), "n_elm mismatch"
    print("Verification passed.")

    # Benchmark
    def original_loop():
        p_act = np.zeros(101)
        n_elm = np.zeros(101)
        for i in range(len(j_star)):
            p_act[j_star[i]] += p.iloc[i]
            n_elm[j_star[i]] += 1*j_cond[i]

    def optimized_loop():
        p_act = np.zeros(101)
        n_elm = np.zeros(101)
        np.add.at(p_act, j_star, p.values)
        np.add.at(n_elm, j_star, j_cond)

    t1 = timeit.timeit(original_loop, number=50)
    t2 = timeit.timeit(optimized_loop, number=50)

    print(f"Original (50 runs): {t1:.6f} s")
    print(f"Optimized (50 runs): {t2:.6f} s")
    print(f"Speedup: {t1/t2:.2f}x")

if __name__ == "__main__":
    benchmark_accumulation()
