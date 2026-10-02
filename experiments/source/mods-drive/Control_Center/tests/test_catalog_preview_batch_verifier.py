import json
import tempfile
import unittest
from pathlib import Path

from tools.plan_catalog_preview_batch import build_plan
from tools.verify_catalog_preview_batch import verify


class CatalogPreviewBatchVerifierTests(unittest.TestCase):
    def setUp(self):
        self.matrix = Path("research/templates/catalog_preview_probe_matrix.json")

    def test_current_plan_is_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            plan_path = Path(temp) / "plan.json"
            plan_path.write_text(json.dumps(build_plan(self.matrix, "test")), encoding="utf-8")
            result = verify(plan_path, self.matrix, "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z")
        self.assertTrue(result["valid"], result["errors"])

    def test_changed_matrix_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            plan_path = temp_path / "plan.json"
            plan_path.write_text(json.dumps(build_plan(self.matrix, "test")), encoding="utf-8")
            changed = temp_path / "matrix.json"
            changed.write_text(self.matrix.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            result = verify(plan_path, changed)
        self.assertFalse(result["valid"])
        self.assertTrue(any("hash" in error for error in result["errors"]))

    def test_unsafe_policy_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            plan_path = Path(temp) / "plan.json"
            plan = build_plan(self.matrix, "test")
            plan["execution_policy"]["stable_profile_allowed"] = True
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            result = verify(plan_path, self.matrix)
        self.assertFalse(result["valid"])
        self.assertTrue(any("stable_profile_allowed" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
