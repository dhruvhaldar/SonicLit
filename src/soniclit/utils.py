import os
import zipfile

def safe_extract_zip(zip_ref, target_dir):
    """
    Extracts a zip file to the target directory, preventing path traversal attacks.

    Args:
        zip_ref (zipfile.ZipFile): The zip file object to extract.
        target_dir (str): The directory to extract files into.

    Raises:
        ValueError: If a file in the zip attempts to write outside the target directory.
    """
    target_dir = os.path.abspath(target_dir)

    for member in zip_ref.namelist():
        member_path = os.path.abspath(os.path.join(target_dir, member))

        if os.path.commonpath([target_dir, member_path]) != target_dir:
            raise ValueError(f"Zip Slip vulnerability detected: {member}")

    zip_ref.extractall(target_dir)
