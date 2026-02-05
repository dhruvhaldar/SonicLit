## 2025-02-18 - [PSD Calculation Optimization & Bug Fix]
**Learning:** Found an inefficient pattern `abs(z * conj(z))` for calculating Power Spectral Density in numpy. This involves complex multiplication and square root (in `abs`).
**Action:** Replace with `z.real**2 + z.imag**2` which is purely real arithmetic and avoids intermediate complex array allocations. Also learned that variable shadowing (importing a module with same name as a common argument) caused hidden bugs in this codebase preventing tests from running.
