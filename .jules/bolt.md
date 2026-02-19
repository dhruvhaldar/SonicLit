## 2026-02-05 - FWH Loop Optimization
**Learning:** In sliding-window algorithms where `f(t)` derivatives are calculated using neighbors (e.g., `(f(t+dt)-f(t-dt))/2dt`), the "future" term of step `j` often becomes the "past" term of step `j+1`. Caching this value avoids recomputing the entire term (which may involve array operations).
**Action:** When optimizing time-marching loops, explicitly check for data reuse opportunities between iterations.

## 2026-02-05 - Linear Interpolation Optimization
**Learning:** `(1-w)*A + w*B` involves 2 multiplications and 1 addition. `A + w*(B-A)` involves 1 multiplication and 2 additions. Since multiplication is generally more expensive than addition (and FMA might apply), the second form is often faster for large arrays.
**Action:** Prefer `A + w*(B-A)` for linear interpolation in tight loops.

## 2026-02-05 - MPI Loop Optimization
**Learning:** In MPI-parallel loops where workers receive full data arrays (e.g. via `gather` then `bcast`) but only process a local partition, re-scattering the local partition (which they already have access to) is a massive performance anti-pattern.
**Action:** Slice global arrays into local partitions immediately upon receipt/creation, and perform all subsequent operations on local slices. Avoid redundant `comm.scatter` calls inside loops.

## 2026-02-19 - FWH Solver Optimization: Matplotlib Bottleneck
**Learning:** Optimizing the core numerical solver (file I/O + spline interpolation) yielded a 6x speedup for the solver itself, but the total runtime was still dominated (80%) by Matplotlib figure generation (PNG saving) which happens per observer. The solver optimization was masked in simple benchmarks by the heavy visualization overhead.
**Action:** When optimizing scientific code with integrated visualization, verify if the visualization (I/O, rendering) is the bottleneck. Consider separating computation and visualization to measure true impact.
