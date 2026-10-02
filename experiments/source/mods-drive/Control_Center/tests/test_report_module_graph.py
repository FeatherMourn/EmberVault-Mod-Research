import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ReportModuleGraphTests(unittest.TestCase):
    def test_strict_metadata_flag_is_reported_and_finds_legacy_modules(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"
            (root / "legacy").mkdir(parents=True)
            (root / "legacy" / "module.json").write_text(
                json.dumps({"id": "legacy"}), encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, "tools/report_module_graph.py", str(root), "--strict-metadata"],
                cwd=Path(__file__).parents[1], capture_output=True, text=True, check=False,
            )
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 2)
            self.assertTrue(report["strict_metadata"])
            self.assertTrue(any("valid feature_state" in issue["message"]
                                for issue in report["issues"]))


if __name__ == "__main__":
    unittest.main()
