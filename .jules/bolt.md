## 2025-02-27 - Cubic Spline Optimization in FWH Solver
**Learning:** In the `stationary_serial` and `stationary_parallel` loops of the FWH solver, `cubic_spline` interpolation is performed three times (for `Qn`, `Lr`, `Lm`) using the same `interpolation_weight`. By precomputing the 4 polynomial coefficients outside the variable-specific calls (but inside the time loop), we reduce the operation count from ~60 ops/step to ~21 ops/step for the spline part. This yielded a ~2.7x speedup for the spline calculation itself.
**Action:** Always check for repeated expensive calculations inside loops that share common inputs (like interpolation weights) and hoist them out or precompute shared factors.

## 2025-02-27 - I/O Bottleneck in FWH Solver
**Learning:** The `stationary_serial` implementation reads a new CSV file for every time step (`calculate_source_terms_serial`). This I/O operation dominates the execution time (e.g., >95% of time for typical cases). CPU optimizations like vectorized math or spline precomputation, while effective in isolation, have limited impact on the total wall time unless I/O is also optimized (e.g., by reading all files at once or using a binary format).
**Action:** When optimizing data-heavy loops, profile I/O vs Compute first. Future optimizations should focus on file handling strategy.

## 2025-02-27 - Numpy Dot Product Overhead
**Learning:** For small vector operations (e.g., dot product of a (N,3) array with a (3,) vector), explicit component-wise multiplication and summation in Python (`A[:,0]*v[0] + ...`) can be faster than `np.dot(A, v)` due to the overhead of numpy dispatch and broadcasting for small dimensions.
**Action:** Be cautious with `np.dot` inside tight loops or on small dimensions; explicit unrolling might be faster.

## 2025-02-27 - DataFrame Overhead in Loop
**Learning:** Creating a `pd.DataFrame` inside a tight loop (like in `calculate_source_terms_serial`) adds significant overhead, especially when only the underlying numpy arrays are needed immediately after. Replacing the DataFrame return with a simple dictionary of numpy arrays yielded a ~7% performance improvement in the FWH solver's serial execution.
**Action:** Avoid constructing Pandas DataFrames in performance-critical loops if the data can be passed as a dictionary of NumPy arrays or a similar lightweight structure.

## 2024-05-24 - I/O Optimization in Loop-Based Solvers
**Learning:** In heavily I/O bound loop-based solvers (like time-marching FWH), reducing the number of columns read by `pd.read_csv` using `usecols` is a critical optimization. Even if `engine='c'` is used, parsing unused columns (like 'temperature' in `fwh_solver.py`) adds significant cumulative overhead.
**Action:** Always audit `pd.read_csv` calls inside loops to ensure only strictly necessary columns are being parsed.

## 2024-05-24 - Vectorization Pitfalls in Broadcasting
**Learning:** Implicit broadcasting in NumPy can fail silently or misleadingly if dimensions are not explicitly managed. In `fwh_solver.py`, `ambient_density` (N,) * `U0` (3,) failed because it required `ambient_density[:, None]` to broadcast to (N,3).
**Action:** When performing element-wise multiplication between arrays of different ranks (e.g., scalar field * vector field), always use explicit reshaping (e.g., `[:, None]`) to ensure correct broadcasting behavior.

## 2025-02-18 - Vector Optimization in FWH Solver
**Learning:** In NumPy, calculating `np.sum((A + B) * C, axis=1)` where A, B, C are large (N, 3) arrays involves creating a temporary intermediate array (A+B) of size (N, 3). It is more memory-efficient and often faster to compute `np.sum(A * C, axis=1) + np.sum(B * C, axis=1)` if A and B are constructed from smaller components (e.g., broadcasting). Specifically, `(-rho0 * U0 + rho * v) . n` is better computed as `-rho0 * (U0 . n) + rho * (v . n)`.
**Action:** When optimizing vector equations, look for opportunities to decompose terms to avoid large intermediate array allocations, especially when dot products reduce dimensionality.
