import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VisualCandidateDependencyTests(unittest.TestCase):
    def test_reports_available_and_missing_guids(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            archive = root / "archive"
            archive.mkdir()
            candidate = root / "candidate.json"
            available = "11111111-1111-1111-1111-111111111111"
            missing = "22222222-2222-2222-2222-222222222222"
            candidate.write_text(json.dumps({"material": available, "nested": [missing]}))
            (archive / f"{available}_0.json").write_text("{}")
            result = subprocess.run(
                [sys.executable, "tools/report_visual_candidate_dependencies.py", str(candidate), str(archive)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            report = json.loads(result.stdout)
            self.assertEqual(report["unique_dependency_count"], 2)
            self.assertEqual(report["available_count"], 1)
            self.assertEqual(report["missing_count"], 1)


if __name__ == "__main__":
    unittest.main()
