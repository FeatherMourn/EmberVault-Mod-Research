import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CapabilitySnapshotTests(unittest.TestCase):
    def test_reporter_selects_latest_research_inputs_when_defaults_are_used(self):
        source = (Path(__file__).parents[1] / "tools" / "report_capability_snapshot.py").read_text(encoding="utf-8")
        self.assertIn('latest_research_file(root, "CAPABILITY_AUDIT_*.json"', source)
        self.assertIn('latest_research_file(root, "MILESTONE_QUALITY_GATE_*.json"', source)
        self.assertIn('latest_research_file(root, "live_preflight_*.json"', source)
        self.assertIn('latest_research_file(root, "SAFE_METADATA_RESOURCE_TYPES_*.json"', source)
    def test_explicit_test_count_is_written(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "snapshot.json"
            result = subprocess.run(
                [sys.executable, "tools/report_capability_snapshot.py", "--test-count", "999", "--output", str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["test_count"], 999)

    def test_default_evidence_paths_generate_a_current_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "snapshot.json"
            result = subprocess.run(
                [sys.executable, "tools/report_capability_snapshot.py", "--output", str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            snapshot = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["schema"], "control_center.capability_snapshot.v1")
            self.assertTrue(snapshot["inputs"]["capability_audit"].endswith("CAPABILITY_AUDIT_20260927.json"))
            self.assertTrue(snapshot["inputs"]["metadata_policy"].endswith("SAFE_METADATA_RESOURCE_TYPES_20260928.json"))
            self.assertTrue(snapshot["milestone_passed"])
            self.assertTrue(snapshot["metadata_policy"]["compatible"])


if __name__ == "__main__":
    unittest.main()
