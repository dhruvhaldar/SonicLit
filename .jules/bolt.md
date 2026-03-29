## 2024-05-24 - Polynomial Array Factorization Optimization
**Learning:** Refactoring polynomial expressions on NumPy arrays (like cubic splines) to combine scalar multipliers (e.g. `w * (1.0/6.0)`) and group terms to avoid redundant temporary negative arrays (e.g. replacing `-w_sq + w` with positive groupings) avoids intermediate memory allocations and negation ops, yielding a significant (~25%) speedup in array-heavy code.
**Action:** Always inspect polynomial calculations inside performance-critical loops to mathematically factorize terms to use positive evaluations and group constants.
## 2024-05-24 - Polynomial Array Factorization Optimization
**Learning:** Refactoring polynomial expressions on NumPy arrays (like cubic splines) to combine scalar multipliers (e.g. `w * (1.0/6.0)`) and group terms to avoid redundant temporary negative arrays (e.g. replacing `-w_sq + w` with positive groupings) avoids intermediate memory allocations and negation ops, yielding a significant (~25%) speedup in array-heavy code.
**Action:** Always inspect polynomial calculations inside performance-critical loops to mathematically factorize terms to use positive evaluations and group constants.

## 2024-05-24 - Polynomial Array Factorization Optimization
**Learning:** Refactoring polynomial expressions on NumPy arrays (like cubic splines) to combine scalar multipliers (e.g. `w * (1.0/6.0)`) and group terms to avoid redundant temporary negative arrays (e.g. replacing `-w_sq + w` with positive groupings) avoids intermediate memory allocations and negation ops, yielding a significant (~25%) speedup in array-heavy code.
**Action:** Always inspect polynomial calculations inside performance-critical loops to mathematically factorize terms to use positive evaluations and group constants.

## 2025-02-19 - Cross-Spectrum CPSD Magnitude Optimization
**Learning:** In NumPy, when computing the magnitude of the product of two complex arrays (e.g. `np.abs(a * b)` vs `np.abs(a) * np.abs(b)`), computing the product first and then taking the absolute value (`np.abs(a * b)`) is significantly faster (~20-25% speedup) because it avoids allocating multiple large intermediate arrays for the individual magnitudes.
**Action:** When calculating cross power spectral density (CPSD) magnitudes or similar compound complex magnitude operations, use `np.abs(a * b)` instead of `np.abs(a) * np.abs(b)` or mathematically equivalent `np.abs(a * np.conj(b))`.
