import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_furniture_matrix_evidence import verify


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research" / "probe_sessions" / "furniture_donor_matrix_runtime_evidence_20260928.json"


class FurnitureMatrixEvidenceTests(unittest.TestCase):
    def test_current_three_donor_evidence_is_valid(self):
        result = verify(EVIDENCE)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["run_count"], 3)

    def test_duplicate_clone_ids_fail_closed(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        data["runs"][1]["clone_item_id"] = data["runs"][0]["clone_item_id"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = verify(path)
        self.assertFalse(result["valid"])
        self.assertIn("clone item IDs are duplicated", result["errors"])

    def test_duplicate_donors_fail_closed(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        data["runs"][1]["donor_item_id"] = data["runs"][0]["donor_item_id"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = verify(path)
        self.assertFalse(result["valid"])
        self.assertIn("donor item IDs are duplicated", result["errors"])
