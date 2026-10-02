import unittest
from pathlib import Path

from tools.plan_catalog_preview_batch import build_plan


class CatalogPreviewBatchTests(unittest.TestCase):
    def test_plan_is_deterministic_except_timestamp(self):
        matrix = Path("research/templates/catalog_preview_probe_matrix.json")
        first = build_plan(matrix, "test")
        second = build_plan(matrix, "test")
        self.assertEqual(first["matrix_sha256_prefix"], second["matrix_sha256_prefix"])
        self.assertEqual(first["runs"], second["runs"])
        self.assertEqual([run["item_id"] for run in first["runs"]], [run["item_id"] for run in second["runs"]])

    def test_plan_is_isolated_and_complete(self):
        plan = build_plan(Path("research/templates/catalog_preview_probe_matrix.json"), "test")
        self.assertFalse(plan["execution_policy"]["stable_profile_allowed"])
        self.assertEqual(len(plan["runs"]), 4)
        self.assertEqual(len({run["item_id"] for run in plan["runs"]}), 4)

    def test_plan_carries_candidate_field_strategy(self):
        plan = build_plan(Path("research/templates/catalog_preview_probe_matrix.json"), "test")
        image = plan["runs"][0]
        self.assertEqual(image["item_fields"], ["iconImage"])
        self.assertIn("iconModel", image["preserve_fields"])
        ui = plan["runs"][3]
        self.assertIn("icons", ui["ui_fields"])
        self.assertTrue(ui["schema_paths"])


if __name__ == "__main__":
    unittest.main()
