import pytest
import os
import zipfile
import shutil
import tempfile
import stat
from soniclit.utils import safe_extract_zip

class TestZipSecurity:

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_zip_slip_protection(self, temp_dir):
        # Create malicious zip
        zip_path = os.path.join(temp_dir, "slip.zip")
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("../evil.txt", "hacked")

        extract_to = os.path.join(temp_dir, "extracted_slip")
        os.makedirs(extract_to)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            with pytest.raises(ValueError, match="Zip Slip vulnerability detected"):
                safe_extract_zip(zf, extract_to)

    def test_zip_bomb_protection_size(self, temp_dir):
        # Create a zip bomb (10MB zeros)
        # Set limit to 1MB
        zip_path = os.path.join(temp_dir, "bomb.zip")
        # 10MB
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("bomb.txt", "0" * (10*1024*1024))

        extract_to = os.path.join(temp_dir, "extracted_bomb")
        os.makedirs(extract_to)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Should fail if limit is 1MB
            with pytest.raises(ValueError, match="Zip Bomb detected: .* too large"):
                safe_extract_zip(zf, extract_to, max_size=1*1024*1024)

    def test_zip_bomb_protection_ratio(self, temp_dir):
        # Create a highly compressible file (10MB zeros)
        # Ratio will be ~10000
        # Set max_ratio to 10
        zip_path = os.path.join(temp_dir, "ratio.zip")
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("ratio.txt", "0" * (10*1024*1024))

        extract_to = os.path.join(temp_dir, "extracted_ratio")
        os.makedirs(extract_to)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            with pytest.raises(ValueError, match="Zip Bomb detected: high compression ratio"):
                safe_extract_zip(zf, extract_to, max_ratio=10)

    def test_valid_extraction(self, temp_dir):
        # Create valid zip
        zip_path = os.path.join(temp_dir, "valid.zip")
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("valid.txt", "hello world")

        extract_to = os.path.join(temp_dir, "extracted_valid")
        os.makedirs(extract_to)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            safe_extract_zip(zf, extract_to)

        assert os.path.exists(os.path.join(extract_to, "valid.txt"))
        with open(os.path.join(extract_to, "valid.txt")) as f:
            assert f.read() == "hello world"

    def test_symlink_rejection(self, temp_dir):
        # Create zip with symlink (manually setting external_attr)
        zip_path = os.path.join(temp_dir, "symlink.zip")

        # We need to use ZipInfo to set external_attr
        zip_info = zipfile.ZipInfo("evil_link")
        # 0xA000 is S_IFLNK (symbolic link)
        permissions = 0o777
        zip_info.external_attr = (stat.S_IFLNK | permissions) << 16

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr(zip_info, "/etc/passwd")

        extract_to = os.path.join(temp_dir, "extracted_symlink")
        os.makedirs(extract_to)

        with zipfile.ZipFile(zip_path, 'r') as zf:
             with pytest.raises(ValueError, match="Symlink detected"):
                safe_extract_zip(zf, extract_to)
