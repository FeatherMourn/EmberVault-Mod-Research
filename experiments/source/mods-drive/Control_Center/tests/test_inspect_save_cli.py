import subprocess
import sys
import unittest
from pathlib import Path


class InspectSaveCliTests(unittest.TestCase):
    def test_help_is_available(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "tools/inspect_save.py", "--help"], cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("without writing", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
