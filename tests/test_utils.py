import unittest
import os
import shutil
import zipfile
import tempfile
from soniclit.utils import safe_extract_zip, validate_zip_contents

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.zip_path = os.path.join(self.test_dir, "test.zip")
        self.extract_dir = os.path.join(self.test_dir, "extract")
        os.makedirs(self.extract_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_safe_extract_zip_valid(self):
        # Create a valid zip
        with zipfile.ZipFile(self.zip_path, 'w') as zf:
            zf.writestr('file1.txt', 'content1')
            zf.writestr('dir1/file2.txt', 'content2')

        with zipfile.ZipFile(self.zip_path, 'r') as zf:
            safe_extract_zip(zf, self.extract_dir)

        self.assertTrue(os.path.exists(os.path.join(self.extract_dir, 'file1.txt')))
        self.assertTrue(os.path.exists(os.path.join(self.extract_dir, 'dir1/file2.txt')))

    def test_safe_extract_zip_malicious(self):
        # Create a malicious zip
        with zipfile.ZipFile(self.zip_path, 'w') as zf:
            zf.writestr('../evil.txt', 'evil content')

        with zipfile.ZipFile(self.zip_path, 'r') as zf:
            with self.assertRaises(ValueError) as cm:
                safe_extract_zip(zf, self.extract_dir)
            self.assertIn("Zip Slip vulnerability detected", str(cm.exception))

        # Verify file was not written outside
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, 'evil.txt')))

    def test_validate_zip_contents(self):
        # Valid Case
        with zipfile.ZipFile(self.zip_path, 'w') as zf:
            zf.writestr('testAvg.csv', 'dummy')

        with open(self.zip_path, 'rb') as f:
            valid, msg = validate_zip_contents(f, "Avg.csv")
            self.assertTrue(valid)
            self.assertIn("Found testAvg.csv", msg)
            self.assertEqual(f.tell(), 0) # Check pointer reset

        # Invalid Case (wrong suffix)
        with zipfile.ZipFile(self.zip_path, 'w') as zf:
            zf.writestr('test.txt', 'dummy')

        with open(self.zip_path, 'rb') as f:
            valid, msg = validate_zip_contents(f, "Avg.csv")
            self.assertFalse(valid)
            self.assertIn("No file ending with", msg)

        # Invalid Case (not a zip)
        with open(self.zip_path, 'w') as f:
            f.write("not a zip")

        with open(self.zip_path, 'rb') as f:
            valid, msg = validate_zip_contents(f, "Avg.csv")
            self.assertFalse(valid)
            self.assertIn("Invalid ZIP", msg)

if __name__ == '__main__':
    unittest.main()
