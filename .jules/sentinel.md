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
