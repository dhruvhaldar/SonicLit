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
