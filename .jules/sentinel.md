## 2026-02-06 - Zip Slip Vulnerability in File Upload
**Vulnerability:** Found a "Zip Slip" vulnerability in the Streamlit web app (`src/soniclit/gui/web/app.py`). The application was using `zipfile.ZipFile.extractall()` on user-uploaded zip files without validating the paths of the files inside the archive. This allowed attackers to overwrite files outside the target directory using relative paths (e.g., `../../etc/passwd`).
**Learning:** Python's standard `zipfile` module does not prevent path traversal by default. `extractall()` blindly trusts the paths in the zip archive. Developers often assume standard libraries are secure by default.
**Prevention:** Always validate file paths before extraction. Implement a helper function (like `safe_extract_zip`) that resolves the absolute path of the destination and checks if it starts with the intended target directory path. Never use `extractall()` on untrusted input without this check.

## 2026-02-12 - Secure Zip Extraction Enhancements
**Vulnerability:** Standard `zipfile` extraction is vulnerable to Zip Bombs (DoS) and Symlink attacks (LFI/RCE potential).
**Learning:** Checking for path traversal (Zip Slip) is not enough. Malicious zips can exhaust resources (Bomb) or write symlinks to sensitive files. `zipfile.ZipInfo.external_attr` encodes file permissions and type (e.g. `S_IFLNK`).
**Prevention:** Enhanced `safe_extract_zip` to check:
1. Uncompressed size limits (individual and total).
2. Compression ratio limits.
3. Symbolic link detection via `external_attr`.
4. Use `extract()` instead of `extractall()` for granular control.

## 2026-02-14 - SSRF in Pandas Library Functions
**Vulnerability:** Found a Server-Side Request Forgery (SSRF) vulnerability in `soniclit.fwh_solver.stationary_serial`. The function blindly passed user-controlled `surf_file` paths to `pd.read_csv`. `pandas` supports URL protocols (http, https, ftp, s3) natively, allowing attackers to make the server fetch remote resources.
**Learning:** Data science libraries like `pandas` often include powerful I/O features (like URL fetching) that are not secure by default when exposed to untrusted input. Library functions that take file paths as strings must treat them as potential URLs.
**Prevention:** Validate file paths before passing them to `pd.read_csv` or similar functions. Explicitly block `://` or restrict inputs to local filesystem paths if remote access is not intended. Added a check `if "://" in surf_file: raise ValueError(...)`.

## 2026-02-09 - DoS Prevention in Streamlit Inputs
**Vulnerability:** The Streamlit web app (`src/soniclit/gui/web/app.py`) allowed unlimited integer input for `steps_val` (Number of Steps) and `chunks`. An attacker could input a massive number (e.g., 10^9), causing the application to allocate huge arrays (Memory Exhaustion) or perform excessive computations (CPU Exhaustion), leading to a Denial of Service (DoS).
**Learning:** Framework widgets like `st.number_input` do not enforce upper bounds by default unless `max_value` is specified. Even if specified, frontend validation can be bypassed. Backend logic must always clamp or validate inputs before using them in resource-intensive operations.
**Prevention:**
1. Explicitly set `min_value` and `max_value` on all numeric inputs.
2. Add backend clamping logic (e.g., `val = min(val, LIMIT)`) immediately after receiving input.
3. Validate the length and structure of complex inputs (e.g., lists parsed via `ast.literal_eval`) to prevent recursion or massive loops.

## 2026-02-15 - DoS Protection for Complex Input Parsing
**Vulnerability:** The Streamlit app used `ast.literal_eval` on potentially unlimited string inputs (`Observer Locations`, `Mach Number`). An attacker could supply a massive string (e.g., 100MB) causing the server to hang or crash due to resource exhaustion (DoS) during parsing.
**Learning:** Python's `ast.literal_eval` is safe from code execution but not from resource exhaustion. Frontend constraints (like `max_chars`) improve UX but do not protect the backend API.
**Prevention:**
1. Enforce strict length limits on string inputs using `len()` checks before expensive parsing operations.
2. Use `max_chars` in frontend widgets as a first line of defense (UX).
3. Validate structure and depth of parsed objects (e.g., list length) immediately after parsing.
