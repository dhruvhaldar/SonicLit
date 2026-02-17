## 2026-02-05 - FWH Loop Optimization
**Learning:** In sliding-window algorithms where `f(t)` derivatives are calculated using neighbors (e.g., `(f(t+dt)-f(t-dt))/2dt`), the "future" term of step `j` often becomes the "past" term of step `j+1`. Caching this value avoids recomputing the entire term (which may involve array operations).
**Action:** When optimizing time-marching loops, explicitly check for data reuse opportunities between iterations.

## 2026-02-05 - Linear Interpolation Optimization
**Learning:** `(1-w)*A + w*B` involves 2 multiplications and 1 addition. `A + w*(B-A)` involves 1 multiplication and 2 additions. Since multiplication is generally more expensive than addition (and FMA might apply), the second form is often faster for large arrays.
**Action:** Prefer `A + w*(B-A)` for linear interpolation in tight loops.
