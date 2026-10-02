import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_tuning_coverage import verify


class TuningCoverageVerifierTests(unittest.TestCase):
    def test_current_queue_is_valid(self):
        root = Path(__file__).resolve().parents[1]
        self.assertTrue(verify(root / "research" / "TUNING_RESEARCH_QUEUE_20260928.json")["valid"])

    def test_wrong_build_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "coverage.json"
            path.write_text(json.dumps({"schema": "control_center.tuning_coverage.v1", "build": "old", "families": [], "research_queue": []}), encoding="utf-8")
            self.assertFalse(verify(path)["valid"])


if __name__ == "__main__":
    unittest.main()
