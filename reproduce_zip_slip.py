import zipfile
import os
import shutil

def test_zip_slip():
    # Create a malicious zip file
    malicious_zip = "malicious.zip"
    target_file = "hacked.txt"

    # We want to write to the current directory, escaping the extract directory
    # If we extract to ./temp_extract_dir, we want to write to ./hacked.txt
    # So the path in zip should be ../hacked.txt

    with zipfile.ZipFile(malicious_zip, 'w') as zf:
        zf.writestr('../' + target_file, "YOU HAVE BEEN HACKED")

    with zipfile.ZipFile(malicious_zip, 'r') as zf:
        print(f"Zip content: {zf.namelist()}")

    # Create extraction directory
    extract_dir = os.path.abspath("temp_extract_dir")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)

    print(f"Extracting {malicious_zip} to {extract_dir}...")

    try:
        with zipfile.ZipFile(malicious_zip, 'r') as zf:
            zf.extractall(extract_dir)

        # Check if the file was written outside
        expected_path = os.path.abspath(target_file)
        print(f"Checking for existence of {expected_path}")
        if os.path.exists(expected_path):
            print(f"VULNERABILITY CONFIRMED: File written to {expected_path}")
            # cleanup
            os.remove(expected_path)
        else:
            print("Vulnerability failed to reproduce: File not found outside directory.")
            # Check where it went
            inside_path = os.path.join(extract_dir, target_file)
            if os.path.exists(inside_path):
                 print(f"File was written inside: {inside_path} (stripped?)")
            else:
                 # Check recursively
                 for root, dirs, files in os.walk(extract_dir):
                     for file in files:
                         print(f"Found file: {os.path.join(root, file)}")


    except Exception as e:
        print(f"Extraction failed: {e}")

    # Cleanup
    if os.path.exists(malicious_zip):
        os.remove(malicious_zip)
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)

if __name__ == "__main__":
    test_zip_slip()
