import os
import zipfile
import stat

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

def predict_column_roles(columns):
    """
    Predicts which columns in a dataframe correspond to 'Time' and 'Signal'.

    Args:
        columns (list): List of column names (str).

    Returns:
        tuple: (time_col_index, sig_col_index)

    Example:
        >>> cols = ['Pressure', 'Time', 'Velocity']
        >>> predict_column_roles(cols)
        (1, 0)
    """
    time_col_idx = 0
    sig_col_idx = 0

    # Heuristic for Time: look for "time", "t", "date", "timestamp"
    # We prefer exact match "time" or "t", then containing "time".

    best_score = -1 # 0: contains time, 1: equals time/t

    for i, col in enumerate(columns):
        c = str(col).lower() # Ensure string
        score = -1
        if c == 'time' or c == 't':
            score = 1
        elif 'time' in c or 'date' in c or 'timestamp' in c:
            score = 0

        if score > best_score:
            best_score = score
            time_col_idx = i
            if score == 1:
                break

    # Heuristic for Signal: first column that is NOT the predicted time column
    if len(columns) > 1:
        for i in range(len(columns)):
            if i != time_col_idx:
                sig_col_idx = i
                break
    else:
        sig_col_idx = 0

    return time_col_idx, sig_col_idx
