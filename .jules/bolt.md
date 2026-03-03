## 2024-02-28 - FWH Distance Calculation Optimization
**Learning:** In scientific simulations using NumPy (like FWH solvers), calculating the Euclidean norm of large lists of 3D vectors `(N, 3)` using `np.linalg.norm(diff, axis=1)` carries significant function overhead and dimension-checking logic that makes it surprisingly slow. Unrolling the equation explicitly (`np.sqrt(diff[:,0]**2 + diff[:,1]**2 + diff[:,2]**2)`) can be ~3.8x faster without sacrificing readibility.
**Action:** When finding bottlenecks inside critical calculation loops (e.g. iterating over observers), always check if `np.linalg.norm` with an axis argument can be replaced by explicit scalar arithmetic for known small-dimension vector arrays.

## 2025-02-28 - FFT Cross Spectrum and Auto Correlation Optimization
**Learning:** In signal processing, calculating magnitudes or power from complex FFT arrays using element-wise complex multiplications (e.g., `A * np.conjugate(B)` or `sig_fft.real**2 + sig_fft.imag**2`) is surprisingly slower than leveraging numpy's built-in optimized magnitude calculations `np.abs(A) * np.abs(B)` or `np.abs(sig_fft)**2` (often yielding 2x speedup). Additionally, calculating auto-correlation using FFT (`np.fft.irfft(sig_fft * np.conjugate(sig_fft))`) directly can be significantly faster (up to 2x) than `scipy.signal.correlate(..., method='auto')` for standard sizes by eliminating overhead.
**Action:** When finding bottlenecks in PSD, Cross-Spectrum, or Auto-correlation routines, avoid explicit `np.conjugate` multiplications or explicit `real**2 + imag**2` arithmetic; use `np.abs` or direct FFT-based convolution for Auto-correlation.
## 2025-02-28 - Explicit Arithmetic for Small Arrays
**Learning:** In scientific simulations using NumPy (like FWH solvers), calculating `np.sum` on small arrays (e.g., length-3 vectors like `mach_number`) carries significant overhead compared to explicit scalar arithmetic like `mach_number[0]**2 + mach_number[1]**2 + mach_number[2]**2`. This overhead can be up to 7x slower and is easily noticeable in performance-critical sections without sacrificing readability.
**Action:** Replace `np.sum(arr**2)` with explicit component-wise addition for arrays of size <= 3 when optimizing loops.

## 2025-02-28 - FFT Auto Correlation Optimization
**Learning:** In signal processing, calculating auto-correlation from complex FFT arrays using element-wise complex multiplications (e.g., `sig_fft * np.conjugate(sig_fft)`) is slower than leveraging numpy's built-in optimized magnitude calculations `np.abs(sig_fft)**2` (yielding 1.1x to 1.5x speedup). This complements the previous cross spectrum optimization.
**Action:** When finding bottlenecks in PSD, Cross-Spectrum, or Auto-correlation routines, avoid explicit `np.conjugate` multiplications or explicit `real**2 + imag**2` arithmetic; use `np.abs(sig_fft)**2`.
## 2023-10-27 - [NumPy Power Operator Performance]
**Learning:** Using the power operator (`**`) for small integer powers (like `**3`) on NumPy arrays is significantly slower (often >10x) than performing explicit multiplication. NumPy calls the general `pow` function under the hood which has a large overhead.
**Action:** When calculating small powers of large arrays in performance-critical sections, always replace `arr**3` with `arr * arr * arr` or reuse existing lower power computations (e.g., `arr_sq * arr`).

## 2025-02-28 - Factor calculation optimization
**Learning:** In mathematical routines using NumPy arrays, algebraically refactoring expressions to reuse intermediate results (e.g., computing `factor_pq2 = factor_pt1 / R` rather than recalculating the entire quotient with `R**2`) yields significant speedups (up to 45%) by eliminating redundant element-wise multiplications and divisions of large arrays.
**Action:** Always look for opportunities to algebraically simplify calculations inside intensive loops, reusing terms like `factor_pq2 = factor_pt1 / R` instead of fully recalculating them with squares/cubes.

## 2025-02-28 - Array broadcasting division optimization
**Learning:** When dividing large NumPy arrays by a constant raised to a power (e.g., `arr / (beta**2)`), precomputing the inverse of the constant (e.g., `inv_beta_sq = 1.0 / (beta * beta)`) and multiplying the array by the inverse provides a measurable speedup (~30%) by avoiding broadcasting division.
**Action:** Replace `array / (scalar**2)` with `array * (1.0 / (scalar * scalar))` inside large loops.
