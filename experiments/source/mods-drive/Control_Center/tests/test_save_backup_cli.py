import json
import subprocess
import sys
import unittest
from pathlib import Path


class SaveBackupCliTests(unittest.TestCase):
    def test_discover_is_read_only_and_reports_standard_locations(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "tools/save_backup.py", "discover"], cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema"], "control_center.save_discovery.v1")
        self.assertTrue(report["read_only"])
        self.assertIsInstance(report["candidates"], list)


if __name__ == "__main__":
    unittest.main()
