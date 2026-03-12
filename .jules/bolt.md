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
