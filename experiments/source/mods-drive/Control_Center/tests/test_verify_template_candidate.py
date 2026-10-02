import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class VerifyTemplateCandidateTests(unittest.TestCase):
    def test_cli_reports_valid_single_edge_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "donor.json"
            candidate = root / "candidate.json"
            source.write_text(json.dumps({"components": [
                {"$type": "keen::ecs::Health", "$value": {"max": 10}},
                {"$type": "keen::ecs::ModelResource", "$value": {"model": "donor"}},
            ]}), encoding="utf-8")
            data = json.loads(source.read_text(encoding="utf-8"))
            data["components"][1]["$value"]["model"] = "replacement"
            candidate.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "tools/verify_template_candidate.py",
                 str(source), str(candidate), "replacement"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue(json.loads(result.stdout)["valid"])

    def test_cli_rejects_unplanned_change(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "donor.json"
            candidate = root / "candidate.json"
            source.write_text(json.dumps({"components": [
                {"$type": "keen::ecs::ModelResource", "$value": {"model": "donor"}},
                {"$type": "keen::ecs::Health", "$value": {"max": 10}},
            ]}), encoding="utf-8")
            data = json.loads(source.read_text(encoding="utf-8"))
            data["components"][0]["$value"]["model"] = "replacement"
            data["components"][1]["$value"]["max"] = 99
            candidate.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "tools/verify_template_candidate.py",
                 str(source), str(candidate), "replacement"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 2)
            report = json.loads(result.stdout)
            self.assertFalse(report["valid"])
            self.assertIn("components[1].$value.max", report["unexpected_differences"])


if __name__ == "__main__":
    unittest.main()
