import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class UpdateRecoveryCliTests(unittest.TestCase):
    def test_cli_writes_machine_readable_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "module.json"
            output = root / "plan.json"
            manifest.write_text(json.dumps({"id": "stable", "feature_state": "stable",
                                            "game_build": "new"}), encoding="utf-8")
            result = subprocess.run([
                sys.executable, "tools/plan_update_recovery.py", "old", "new",
                str(manifest), "--output", str(output),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "control_center.update_recovery_plan.v1")
        self.assertEqual(data["compatible_modules"], ["stable"])
        self.assertTrue(data["stale_evidence"])


if __name__ == "__main__":
    unittest.main()
