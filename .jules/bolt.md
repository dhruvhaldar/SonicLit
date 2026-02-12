## 2025-02-27 - Cubic Spline Optimization in FWH Solver
**Learning:** In the `stationary_serial` and `stationary_parallel` loops of the FWH solver, `cubic_spline` interpolation is performed three times (for `Qn`, `Lr`, `Lm`) using the same `interpolation_weight`. By precomputing the 4 polynomial coefficients outside the variable-specific calls (but inside the time loop), we reduce the operation count from ~60 ops/step to ~21 ops/step for the spline part. This yielded a ~2.7x speedup for the spline calculation itself.
**Action:** Always check for repeated expensive calculations inside loops that share common inputs (like interpolation weights) and hoist them out or precompute shared factors.

## 2025-02-27 - I/O Bottleneck in FWH Solver
**Learning:** The `stationary_serial` implementation reads a new CSV file for every time step (`calculate_source_terms_serial`). This I/O operation dominates the execution time (e.g., >95% of time for typical cases). CPU optimizations like vectorized math or spline precomputation, while effective in isolation, have limited impact on the total wall time unless I/O is also optimized (e.g., by reading all files at once or using a binary format).
**Action:** When optimizing data-heavy loops, profile I/O vs Compute first. Future optimizations should focus on file handling strategy.

## 2025-02-27 - Numpy Dot Product Overhead
**Learning:** For small vector operations (e.g., dot product of a (N,3) array with a (3,) vector), explicit component-wise multiplication and summation in Python (`A[:,0]*v[0] + ...`) can be faster than `np.dot(A, v)` due to the overhead of numpy dispatch and broadcasting for small dimensions.
**Action:** Be cautious with `np.dot` inside tight loops or on small dimensions; explicit unrolling might be faster.
