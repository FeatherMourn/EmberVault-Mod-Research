import unittest
from unittest.mock import patch
import json
import tempfile
from pathlib import Path

from tools.run_portable_launch_smoke import process_ids
from tools.verify_portable_launch_smoke import validate


class PortableLaunchRunnerTests(unittest.TestCase):
    def test_process_ids_parses_csv_tasklist(self):
        completed = type("Completed", (), {"stdout": '"EnshroudedModHub.exe","1234","Console","1","10,000 K"\n', "returncode": 0})()
        with patch("tools.run_portable_launch_smoke.subprocess.run", return_value=completed):
            self.assertEqual(process_ids("EnshroudedModHub.exe"), {1234})

    def test_v2_evidence_requires_empty_process_tree(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "evidence.json"
            path.write_text(json.dumps({"schema": "control_center.portable_launch_smoke.v2", "launch_observed": True, "process_responding": True, "clean_shutdown_observed": True, "game_started": False, "status": "passed", "remaining_pids": []}), encoding="utf-8")
            result = validate(path)
            self.assertTrue(result["valid"])
            self.assertEqual(result["schema"], "control_center.portable_launch_smoke_verification.v2")


if __name__ == "__main__":
    unittest.main()
