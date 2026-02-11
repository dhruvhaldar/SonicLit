## 2026-02-08 - [Vectorization vs List Comprehension]
**Learning:** Found an inefficient pattern `np.array([int(k//dt) for k in tau_star])` which iterates in Python. This is significantly slower than vectorized numpy operations.
**Action:** Replace list comprehensions over numpy arrays with vectorized operations like `(tau_star // dt).astype(int)` to leverage C-level loop optimization. Also, remove unused variables allocated before loops to save memory.

## 2025-02-18 - [PSD Calculation Optimization & Bug Fix]
**Learning:** Found an inefficient pattern `abs(z * conj(z))` for calculating Power Spectral Density in numpy. This involves complex multiplication and square root (in `abs`).
**Action:** Replace with `z.real**2 + z.imag**2` which is purely real arithmetic and avoids intermediate complex array allocations. Also learned that variable shadowing (importing a module with same name as a common argument) caused hidden bugs in this codebase preventing tests from running.

## 2025-02-17 - [Optimizing Cubic Spline with NumPy]
**Learning:** Naively vectorizing polynomial evaluation (e.g., cubic spline) can be slower than the original "inefficient" code due to excessive temporary array allocations for intermediate terms. Python's overhead for array creation dominates unless operations are fused or minimized.
**Action:** Use Horner's method and explicitly precompute/share common subexpressions (e.g., diffs) to minimize the number of full-array temporary allocations. Also, be wary of mixed indentation in legacy files causing unexpected `TabError`.

## 2025-05-20 - [Vectorizing Pandas Operations in Hot Loops]
**Learning:** Found that repeatedly calling `pd.DataFrame` operations (arithmetic, filtering) inside a hot loop (time-stepping) creates significant overhead due to index alignment and Python iteration.
**Action:** Convert DataFrames to NumPy arrays (or dictionaries of arrays) *before* entering the loop. Use vectorized NumPy broadcasting and dot products (`np.sum(A * B, axis=1)`) instead of Series element-wise operations. Also, specify `engine='c'` and `dtype=np.float64` in `pd.read_csv` for a measurable I/O boost.

## 2026-03-10 - [Precomputing Loop-Invariant Factors]
**Learning:** In time-marching simulations (like FWH solver), complex geometric factors involving distance ($R$) and Mach number ($M_r$) are often recalculated inside the loop despite being time-independent for stationary observers.
**Action:** Extract these calculations (division, exponentiation) outside the loop. Precompute factors like `1/(R*(1-Mr)**2)` and use simple multiplication inside the loop. This can yield ~2x speedup for the solver loop.

## 2026-03-12 - [Optimizing Weighted Accumulation]
**Learning:** `np.add.at` is convenient for accumulating weighted values into bins, but it is unbuffered and relatively slow for large loops.
**Action:** Use `np.bincount` with `weights` and `minlength` arguments for a ~1.6x speedup on accumulation operations. Ensure `minlength` is precomputed outside the loop to avoid redundant `max()` calls. Also, use explicit element-wise multiplication instead of `np.dot` to robustly handle both scalar and array inputs during vector operations.
