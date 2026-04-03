## 2024-05-24 - Polynomial Array Factorization Optimization
**Learning:** Refactoring polynomial expressions on NumPy arrays (like cubic splines) to combine scalar multipliers (e.g. `w * (1.0/6.0)`) and group terms to avoid redundant temporary negative arrays (e.g. replacing `-w_sq + w` with positive groupings) avoids intermediate memory allocations and negation ops, yielding a significant (~25%) speedup in array-heavy code.
**Action:** Always inspect polynomial calculations inside performance-critical loops to mathematically factorize terms to use positive evaluations and group constants.

## 2024-05-24 - Polynomial Array Factorization Optimization
**Learning:** Refactoring polynomial expressions on NumPy arrays (like cubic splines) to combine scalar multipliers (e.g. `w * (1.0/6.0)`) and group terms to avoid redundant temporary negative arrays (e.g. replacing `-w_sq + w` with positive groupings) avoids intermediate memory allocations and negation ops, yielding a significant (~25%) speedup in array-heavy code.
**Action:** Always inspect polynomial calculations inside performance-critical loops to mathematically factorize terms to use positive evaluations and group constants.

## 2025-02-19 - Cross-Spectrum CPSD Magnitude Optimization
**Learning:** In NumPy, when computing the magnitude of the product of two complex arrays (e.g. `np.abs(a * b)` vs `np.abs(a) * np.abs(b)`), computing the product first and then taking the absolute value (`np.abs(a * b)`) is significantly faster (~20-25% speedup) because it avoids allocating multiple large intermediate arrays for the individual magnitudes.
**Action:** When calculating cross power spectral density (CPSD) magnitudes or similar compound complex magnitude operations, use `np.abs(a * b)` instead of `np.abs(a) * np.abs(b)` or mathematically equivalent `np.abs(a * np.conj(b))`.

## 2025-02-19 - Redundant Math Evaluation Pitfall
**Learning:** Evaluating `np.sqrt(x)` and immediately squaring the result `val * val` is mathematically redundant and incurs an unnecessary function call overhead, yielding massive relative slowdowns for scalar math in hot paths.
**Action:** Avoid mathematically redundant function calls followed by their inverse or negating operations. Computing the final expression directly (e.g., `x`) eliminates the function call overhead entirely.

## 2025-02-19 - Fast Floor for Non-Negative Arrays
**Learning:** For strictly non-negative NumPy arrays, calling `.astype(int)` directly acts identically to `np.floor()` because `int()` casting truncates towards zero. Omitting `np.floor()` bypasses a redundant memory allocation and an O(N) array evaluation, resulting in a ~2x speedup for the floor operation.
**Action:** When calculating integer indices from float arrays that are guaranteed to be non-negative (e.g., relative time calculations `tau - min_tau`), use `arr.astype(int)` instead of `np.floor(arr).astype(int)`.

## 2025-02-23 - Cascaded Scalar Array Scaling Optimization
**Learning:** Computing several scaled versions of complex intermediate array factors by independently calculating unscaled base arrays and multiplying each by various scalar constants causes redundant large array allocations. Chaining the scalar scaling directly into the initial array definition and deriving subsequent scaled factors progressively (e.g., `factor_b = factor_a * scalar`) eliminates large intermediate unscaled array calculations and reduces multiplication overhead, yielding a >2x relative speedup for factor evaluation blocks.
**Action:** When calculating multiple proportional large array terms, mathematically refactor the equations to start with a fully scaled base term and derive dependent terms via consecutive scalar multiplications instead of evaluating distinct heavy expressions.
