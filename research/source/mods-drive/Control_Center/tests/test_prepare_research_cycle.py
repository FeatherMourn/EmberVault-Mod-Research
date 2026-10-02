import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PrepareResearchCycleTests(unittest.TestCase):
    def test_cycle_generates_suite_and_preserves_quarantine(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            policy = root / "policy.json"
            policy.write_text(json.dumps({
                "schema": "control_center.safe_metadata_resource_types.v1",
                "target_build": "test-build",
                "verified_types": [{"type": "keen::ItemInfo"}],
                "quarantined_types": [{"type": "keen::TemplateResource", "reason": "unsafe"}],
            }), encoding="utf-8")
            output = root / "cycle"
            result = subprocess.run(
                [sys.executable, "tools/prepare_research_cycle.py", str(policy), str(output)],
                cwd=Path(__file__).parents[1], capture_output=True, text=True, check=True,
            )
            report = json.loads(result.stdout)
            self.assertEqual(report["target_build"], "test-build")
            self.assertEqual(report["quarantined_types"], ["keen::TemplateResource"])
            self.assertEqual(report["generated_probe_suite"], "metadata_probe_suite")
            self.assertTrue((output / "metadata_probe_suite" / "mod.json").is_file())
            self.assertTrue((output / "RESEARCH_CYCLE.json").is_file())


if __name__ == "__main__":
    unittest.main()
