## 2026-02-08 - [Vectorization vs List Comprehension]
**Learning:** Found an inefficient pattern `np.array([int(k//dt) for k in tau_star])` which iterates in Python. This is significantly slower than vectorized numpy operations.
**Action:** Replace list comprehensions over numpy arrays with vectorized operations like `(tau_star // dt).astype(int)` to leverage C-level loop optimization. Also, remove unused variables allocated before loops to save memory.

## 2025-02-18 - [PSD Calculation Optimization & Bug Fix]
**Learning:** Found an inefficient pattern `abs(z * conj(z))` for calculating Power Spectral Density in numpy. This involves complex multiplication and square root (in `abs`).
**Action:** Replace with `z.real**2 + z.imag**2` which is purely real arithmetic and avoids intermediate complex array allocations. Also learned that variable shadowing (importing a module with same name as a common argument) caused hidden bugs in this codebase preventing tests from running.

## 2025-02-17 - [Optimizing Cubic Spline with NumPy]
**Learning:** Naively vectorizing polynomial evaluation (e.g., cubic spline) can be slower than the original "inefficient" code due to excessive temporary array allocations for intermediate terms. Python's overhead for array creation dominates unless operations are fused or minimized.
**Action:** Use Horner's method and explicitly precompute/share common subexpressions (e.g., diffs) to minimize the number of full-array temporary allocations. Also, be wary of mixed indentation in legacy files causing unexpected `TabError`.
