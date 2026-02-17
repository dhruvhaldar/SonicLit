import os
import zipfile
import stat
import html

def safe_extract_zip(zip_ref, target_dir, max_size=500*1024*1024, max_ratio=100):
    """
    Extracts a zip file to the target directory, preventing path traversal attacks,
    zip bombs, and extraction of symbolic links.

    Args:
        zip_ref (zipfile.ZipFile): The zip file object to extract.
        target_dir (str): The directory to extract files into.
        max_size (int): Maximum allowed total uncompressed size (bytes). Default 500MB.
        max_ratio (float): Maximum allowed compression ratio. Default 100.

    Raises:
        ValueError: If a vulnerability is detected (Zip Slip, Zip Bomb, Symlink).
    """
    target_dir = os.path.abspath(target_dir)
    total_extracted_size = 0

    for member in zip_ref.infolist():
        # Zip Slip check
        member_path = os.path.abspath(os.path.join(target_dir, member.filename))

        if os.path.commonpath([target_dir, member_path]) != target_dir:
            raise ValueError(f"Zip Slip vulnerability detected: {member.filename}")

        # Symlink check
        # external_attr is 4 bytes. Top 2 bytes are Unix mode.
        # Check if it's a symlink (S_IFLNK)
        if (member.external_attr >> 16) & stat.S_IFLNK == stat.S_IFLNK:
            raise ValueError(f"Symlink detected: {member.filename}")

        # Zip Bomb check (Size)
        if member.file_size > max_size:
             raise ValueError(f"Zip Bomb detected: file {member.filename} too large")

        total_extracted_size += member.file_size
        if total_extracted_size > max_size:
             raise ValueError(f"Zip Bomb detected: total extracted size exceeds limit")

        # Zip Bomb check (Ratio)
        # Only check ratio for files larger than 1MB to avoid false positives on small text files
        if member.file_size > 1024*1024:
            if member.compress_size > 0:
                ratio = member.file_size / member.compress_size
                if ratio > max_ratio:
                    raise ValueError(f"Zip Bomb detected: high compression ratio ({ratio:.1f}) for {member.filename}")

        # Extract individual member
        zip_ref.extract(member, target_dir)

def validate_zip_contents(file_obj, required_suffix="Avg.csv"):
    """
    Validates that a zip file contains at least one file with the required suffix.

    Args:
        file_obj: A file-like object (e.g., BytesIO from Streamlit upload).
        required_suffix (str): The suffix to look for (e.g., "Avg.csv").

    Returns:
        tuple: (bool, str) - (True/False, Message)
    """
    import zipfile
    try:
        with zipfile.ZipFile(file_obj, 'r') as z:
            names = z.namelist()
            found = [n for n in names if n.endswith(required_suffix)]
            if found:
                return True, f"Found {found[0]}"
            else:
                return False, f"No file ending with '{required_suffix}' found."
    except zipfile.BadZipFile:
        return False, "Invalid ZIP file."
    except Exception as e:
        return False, f"Error validating ZIP: {str(e)}"
    finally:
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)


def is_file_size_valid(file_obj, max_size_mb):
    """
    Checks if a file's size is within the allowed limit.

    Args:
        file_obj: A file-like object with a .size attribute (e.g. Streamlit UploadedFile).
        max_size_mb (int): Maximum allowed size in megabytes.

    Returns:
        bool: True if file size is valid, False otherwise.
    """
    if hasattr(file_obj, 'size'):
        return file_obj.size <= max_size_mb * 1024 * 1024
    # Fallback if no size attribute (e.g. standard file object), try to get size
    try:
        if hasattr(file_obj, 'seek') and hasattr(file_obj, 'tell'):
            pos = file_obj.tell()
            file_obj.seek(0, os.SEEK_END)
            size = file_obj.tell()
            file_obj.seek(pos)
            return size <= max_size_mb * 1024 * 1024
    except:
        pass
    # If we can't determine size, assume it's unsafe or let it fail elsewhere?
    # Safer to reject if we can't validate.
    return False


def sanitize_markdown(text):
    """
    Sanitizes text to prevent Markdown injection and XSS.
    Escapes HTML characters and replaces brackets to break Markdown links.

    Args:
        text (str): The text to sanitize.

    Returns:
        str: Sanitized text.
    """
    if not isinstance(text, str):
        return str(text)
    # Escape HTML to prevent HTML injection
    safe_text = html.escape(text)
    # Replace brackets to prevent Markdown link injection [text](url)
    safe_text = safe_text.replace('[', '(').replace(']', ')')
    return safe_text


def get_column_index(columns, candidates):
    """
    Finds the index of the first column name that matches one of the candidates (case-insensitive).
    Prioritizes exact matches, then partial matches.
    Returns 0 if no match found.

    Args:
        columns (list): List of column names.
        candidates (list): List of candidate keywords.

    Returns:
        int: Index of the best match or 0.
    """
    if len(columns) == 0:
        return 0

    columns_lower = [str(c).lower() for c in columns]
    candidates_lower = [c.lower() for c in candidates]

    # 1. Exact match
    for cand in candidates_lower:
        if cand in columns_lower:
            return columns_lower.index(cand)

    # 2. Partial match
    for cand in candidates_lower:
        for i, col in enumerate(columns_lower):
            if cand in col:
                return i

    return 0
