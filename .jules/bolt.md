## 2025-05-18 - Factoring Polynomials for Spline Coefficients
**Learning:** Computing polynomial coefficients for interpolation (like cubic splines) directly using powers of an array (e.g. `w_cu = w_sq * w`) requires redundant array allocations and passes.
**Action:** Mathematically factorize polynomial coefficient expressions to minimize the total number of operations per array element and completely eliminate the need to calculate higher-order array powers (like $w^3$). This reduces both memory bandwidth and CPU overhead.
## 2024-05-24 - NumPy In-Place Arithmetic vs Out-of-Place
**Learning:** In NumPy, in-place array arithmetic (e.g., `arr *= float_val`, `np.log10(arr, out=arr)`) is significantly faster (>2x speedup) than out-of-place assignment because it avoids allocating new memory. However, DO NOT use in-place operations if the target array might be an integer type (e.g., from 16-bit PCM audio) and the operation introduces floats, as this raises a `UFuncTypeError`.
**Action:** Use in-place operations when dtypes are certain to be floats (e.g., spectral densities). Avoid them or cast first when operating on uncertain or integer-typed arrays.

## 2025-05-18 - Avoiding `np.var()` Overhead for Zero-Centered Arrays
**Learning:** Calling `np.var(array)` on an array that has already been explicitly zero-centered (e.g., `array -= np.mean(array)`) forces a completely redundant recalculation of the mean (which will evaluate to `~0`) and the subsequent subtracting operation. This introduces significant, unnecessary overhead for large arrays.
**Action:** When calculating the variance of an explicitly zero-centered array, mathematically bypass `np.var()` by explicitly calculating the mean sum of squares directly via the dot product: `np.dot(array, array) / len(array)`. This provides a massive ~20x performance speedup.
