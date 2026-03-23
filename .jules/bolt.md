## 2025-02-28 - Explicit multiplication optimization nuance
**Learning:** While explicit multiplication (`x * x`) is generally faster than the power operator (`x**2`) for simple NumPy array squaring, it can actually perform worse in certain compound expressions (e.g., `cpsd**2 / (psd1 * psd2)` vs `(cpsd * cpsd) / (psd1 * psd2)`).
**Action:** Always benchmark the specific mathematical expression before applying this micro-optimization, as performance depends on how NumPy evaluates the expression as a whole.

## 2025-02-28 - Accumulation Buffer Conditionals
**Learning:** When working with large accumulation buffers in time-stepping loops (e.g., FWH solvers), applying element-wise boundary masks (like `p *= j_cond`) inside the inner loop requires expensive repeated allocation of large boolean arrays.
**Action:** It is significantly faster (~1.8x) to accumulate all data—including out-of-bounds values—and simply slice the final accumulation buffer at the end.

## 2025-02-28 - Avoid Pre-Calculated Static Exponentiations in Outer Loops
**Learning:** Computing powers for arrays, even simple squares (e.g. `arr**2`), involves allocating memory and making multiple computational passes. Computing them inside a loop when the value is constant outside the loop is a redundant operation.
**Action:** In time-stepping and spatial loops such as the FWH observer loop, precomputing scalar squares outside the loop (like `beta_sq = beta * beta` instead of `beta**2` for each observer and time step) shaves off critical ms over multiple iterations.

## 2025-02-28 - Math Simplification for Vector Field Arrays
**Learning:** In numpy calculations applied over massive meshes ($N > 1,000,000$), allocating intermediate $N \times 3$ vector arrays for calculations like computing distances and dot products is expensive. Expanding the dot products mathematically can remove the memory allocation completely and yield significant speedups (over 2x), but it requires care because variables like `d0`, `d1`, `d2` might need to be explicitly managed.
**Action:** Prefer expanding geometric vector relations (e.g., $(L \cdot r)$ using elements of components $d_0, d_1, d_2$) mathematically before array allocations.

## 2025-02-28 - Built-in Min/Max vs NumPy Min/Max
**Learning:** Using Python's built-in `min()` and `max()` on NumPy arrays iterates through elements one-by-one in Python, which is significantly slower compared to `np.min()` and `np.max()`. For large arrays (e.g., $N > 1,000,000$), this causes a massive bottleneck. Additionally, `min()` will fail if the array is completely empty, whereas `np.min()` allows explicit length checking or handles edge cases better.
**Action:** Always replace `min()` and `max()` with `np.min()` and `np.max()` when operating on NumPy arrays to ensure operations stay optimized in C, avoiding slow Python loop overhead. Ensure to guard against empty arrays when replacing `min()` or `max()`.

## 2025-03-11 - Modulo and Floor Division on NumPy Arrays
**Learning:** When calculating fractional weights and integer bins from time vectors (e.g., `interpolation_weight = (tau_star % dt) / dt` and `j_star = (tau_star // dt).astype(int)`), using Python's modulo (`%`) and floor division (`//`) operators directly on NumPy arrays incurs high performance overhead (~2.3x slower) compared to vector multiplication and subtraction.
**Action:** Avoid `%` and `//` for array variables where mathematically equivalent operations exist using base `numpy` primitives. Multiply by the inverse (`inv_dt = 1.0 / dt`) and use `np.floor` followed by integer casting and explicit array subtraction to achieve much faster C-optimized speeds.

## 2025-03-22 - Replacing the struct module loop with SciPy WAV writer
**Learning:** Writing audio data incrementally using Python's `struct.pack('h', ...)` in a tight `for` loop over millions of float samples creates a severe CPU bottleneck and causes `TypeError` string-join bugs in modern Python.
**Action:** Always replace naive, iterative float-to-PCM conversion and byte compilation loops with `np.asarray`, `np.clip`, `.astype(np.int16)`, and `scipy.io.wavfile.write`, yielding order-of-magnitude (10x-15x) speed improvements.

## 2025-03-31 - Fast Array Dot Products
**Learning:** For computing dot products of large arrays of 3D vectors (e.g., `(N, 3)` arrays like `geom_n` and `surfS`), manual component-wise summation (`A[:,0]*B[:,0] + A[:,1]*B[:,1] + A[:,2]*B[:,2]`) is slow. `np.sum(A * B, axis=1)` is even slower due to temporary array allocation. However, `np.einsum('ij,ij->i', A, B)` provides a >2x speedup. For dot products between a massive `(N, 3)` array and a length-3 scalar vector, `np.dot(A, B)` provides a massive >10x speedup by leveraging optimized BLAS routines.
**Action:** Always replace manual component-wise vector multiplications and sums with `np.einsum('ij,ij->i', A, B)` for array-array dot products, and `np.dot(A, B)` for array-vector dot products when operating on large vector collections.

## 2025-04-03 - Reusing Inverse Matrices/Arrays
**Learning:** In NumPy algorithms iterating over complex formulas, you will often find divisions by an array (e.g., `/ R`) located just a few lines after an inverse of the array was calculated (e.g., `inv_R = 1.0 / R`). Replacing the division with multiplication by the precalculated inverse avoids duplicating expensive division operations.
**Action:** In NumPy mathematical routines, actively scan for existing inverses (e.g., `inv_R = 1.0 / R`) within the same loop scope and replace subsequent array divisions (e.g., `geom_dS / R`) with multiplication by the inverse (e.g., `geom_dS * inv_R`) to yield significant speedups.

## 2025-04-10 - Array Division by Scalar and Redundant np.array() Casting
**Learning:** Dividing a NumPy array by a float scalar (e.g., `arr / scalar`) is slower than multiplying by the precomputed inverse (`arr * (1.0 / scalar)`). Furthermore, wrapping the result in `np.array()` (e.g., `np.array(arr / scalar)`) creates a completely redundant memory allocation and copy, as the result of arithmetic operations on NumPy arrays is already a NumPy array. These combined inefficiencies cause measurable overhead in performance-critical loops like FWH observer iterations.
**Action:** Always prefer multiplying arrays by the inverse of a scalar instead of dividing. Never wrap arithmetic operations on NumPy arrays in `np.array()` unless a specific data type conversion or copy is explicitly required. Precompute the scalar inverse (`inv_scalar = 1.0 / scalar`) outside of loops to maximize performance.

## 2025-04-12 - Mathematical Refactoring of Vector Iterators
**Learning:** Evaluating combinations of operations like division by arrays (`/ arr`) and multiplication by independent loop-invariant scalars inside an inner loop causes slower execution than mathematically reorganizing the expressions to compute a combination constant outside the loop, computing array inverses first (`inv_arr = 1.0 / arr`), and reducing the steps inside.
**Action:** When operating heavily on equations within an iterator loop such as observer positions, analyze constants (e.g., `speed_of_sound * inv_4pi`), combine them outside the loop to limit redundant computations per observer step, and factor out denominators into pre-computed inverse arrays.

## 2025-05-15 - Vector Magnitude and Dot Product using Einsum
**Learning:** For computing dot products of large arrays of 3D vectors against themselves or other arrays (e.g., `d0*d0 + d1*d1 + d2*d2` or `n0*d0 + n1*d1 + n2*d2`), `np.einsum('ij,ij->i', A, B)` is significantly faster (~1.5x-2x) than manual component-wise sum of products.
**Action:** Replace manual component-wise sums with `np.einsum` for array operations in performance-critical sections to reduce intermediate allocations and improve speed.

## 2025-06-12 - Fast Array-Vector Dot Products
**Learning:** For computing dot products between a massive `(N, 3)` array (e.g., `geom_n`) and a length-3 scalar vector (e.g., `mach_number`), manual component-wise summation (`A[:,0]*B[0] + A[:,1]*B[1] + A[:,2]*B[2]`) is slow. `np.dot(A, B)` provides a >5x speedup by leveraging optimized BLAS routines.
**Action:** Always replace manual component-wise vector multiplications and sums with `np.dot(A, B)` for array-vector dot products when operating on large vector collections.

## $(date +%Y-%m-%d) - Scalar Power Operation Optimization
**Learning:** In Python, applying the `**` operator with fractional/negative powers (e.g., `x ** -0.5`) on scalar floats relies on generalized exponentiation routines that are significantly slower than standard C-bound `math` module functions like `1.0 / math.sqrt(x)`. Similarly, computing powers of 2 for integers (e.g., `2 ** N`) is slower than the equivalent bitwise left shift `1 << N`.
**Action:** When working with scalar math (especially in tight or hot loops outside of NumPy bounds), always prefer explicit bitwise shifting for integer powers of 2, and use optimized C bindings like `math.sqrt()` combined with division instead of negative fractional powers.

## 2025-06-25 - Mathematical Re-Use and Scalar Sum of Squares Optimization
**Learning:** For calculating the sum of squares of small, fixed-length arrays (e.g., length-3 vectors), explicit scalar multiplication (e.g., `v[0]*v[0] + v[1]*v[1] + v[2]*v[2]`) is measurably faster (~1.5x) than using the power operator (`v[0]**2 + ...`), `np.dot()`, or `np.sum()`. Furthermore, recalculating this same sum multiple times (e.g., once for a magnitude `M2` and again inside a square root `np.sqrt(1 - (v[0]**2 + ...))`) creates unnecessary duplicate operations.
**Action:** Extract the sum of squares into a variable using explicit scalar multiplication when working with small vectors, and reuse this variable for subsequent dependent expressions to avoid redundant calculations.

## 2025-07-20 - Cold Path Micro-optimizations
**Learning:** Optimizing single scalar math operations (e.g., removing a redundant `np.sqrt`) in cold paths (outside main processing loops or before heavy file I/O operations) provides zero measurable impact and constitutes premature micro-optimization. The previous patch failed because it targeted a cold path, committing a violation of the rule to avoid micro-optimizations with no measurable impact.
**Action:** Focus profiling and optimization efforts strictly on hot paths, such as inner loops and large array computations. Do not apply mathematical micro-optimizations to setup or initialization code.

## 2025-10-24 - CSV Loading Optimization
**Learning:** Reading a large CSV file multiple times to extract different columns individually incurs significant I/O and parsing overhead.
**Action:** Always combine column reads into a single `pd.read_csv` call using the `usecols` parameter when extracting multiple arrays from the same file.

## 2024-05-19 - Redundant array scanning
**Learning:** Calling `np.max` on large arrays within inner loops or even cold paths when the value has already been computed earlier is a redundant performance sink.
**Action:** Always check if an expensive aggregation operation like `np.max` or `np.min` has already been run and its result stored in a local variable before re-running it on the same array in the same scope.
