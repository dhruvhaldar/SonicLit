## 2025-02-28 - Explicit multiplication optimization nuance
**Learning:** While explicit multiplication (`x * x`) is generally faster than the power operator (`x**2`) for simple NumPy array squaring, it can actually perform worse in certain compound expressions (e.g., `cpsd**2 / (psd1 * psd2)` vs `(cpsd * cpsd) / (psd1 * psd2)`).
**Action:** Always benchmark the specific mathematical expression before applying this micro-optimization, as performance depends on how NumPy evaluates the expression as a whole.

## 2025-02-28 - Accumulation Buffer Conditionals
**Learning:** When working with large accumulation buffers in time-stepping loops (e.g., FWH solvers), applying element-wise boundary masks (like `p *= j_cond`) inside the inner loop requires expensive repeated allocation of large boolean arrays.
**Action:** It is significantly faster (~1.8x) to accumulate all data—including out-of-bounds values—and simply slice the final accumulation buffer at the end.

## 2025-02-28 - Avoid Pre-Calculated Static Exponentiations in Outer Loops
**Learning:** Computing powers for arrays, even simple squares (e.g. `arr**2`), involves allocating memory and making multiple computational passes. Computing them inside a loop when the value is constant outside the loop is a redundant operation.
**Action:** In time-stepping and spatial loops such as the FWH observer loop, precomputing scalar squares outside the loop (like `beta_sq = beta * beta` instead of `beta**2` for each observer and time step) shaves off critical ms over multiple iterations.
