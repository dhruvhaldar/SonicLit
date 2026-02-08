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
