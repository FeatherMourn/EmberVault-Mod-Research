import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path

from src.recipe_index import export_recipe_handoff, load_recipe_index, lookup_recipe


class RecipeIndexTests(unittest.TestCase):
    def test_same_build_lookup_resolves_only_normalized_records(self):
        payload = {"records": [{"id": "recipe-1", "kind": "donor-recipe",
                                "identity": {"recipe_id": 3531872774},
                                "build_scope": ["1076226"], "state": "blocked",
                                "evidence": ["offline-source"]}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            records = load_recipe_index(path)
        result = lookup_recipe(records, 3531872774, "1076226")
        self.assertEqual(result["state"], "resolved")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["runtime_behavior"], "unverified")

    def test_missing_same_build_recipe_is_explicitly_unresolved(self):
        result = lookup_recipe([], 3531872774, "1076226")
        self.assertEqual(result["state"], "unresolved")
        self.assertEqual(result["matches"], [])
        self.assertIn("normalized same-build", result["reason"])

    def test_recipe_handoff_is_sanitized_and_runtime_bounded(self):
        records = [{"id": "recipe-1", "recipe_id": "3531872774", "build_scope": ["1076226"],
                    "state": "blocked", "confidence": "bounded", "evidence": ["offline"],
                    "open_questions": ["resolve same-build recipe"]}]
        handoff = export_recipe_handoff(records)[0]
        self.assertEqual(handoff["kind"], "donor-recipe")
        self.assertFalse(handoff["runtime_approval"])
        self.assertNotIn("evidence", handoff)

    def test_lookup_command_reports_unresolved_recipe_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.json"
            path.write_text(json.dumps({"records": []}), encoding="utf-8")
            command = [sys.executable, str(Path(__file__).parents[1] / "tools/lookup_recipe.py"), str(path), "3531872774", "--build", "1076226"]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "unresolved")
        self.assertTrue(payload["read_only"])

    def test_authoritative_catalog_keeps_bed_recipe_unresolved(self):
        catalog = Path(__file__).parents[1] / "research" / "catalog_records_20261004.json"
        result = lookup_recipe(load_recipe_index(catalog), 3531872774, "1076226")
        self.assertEqual(result["state"], "unresolved")
        self.assertEqual(result["matches"], [])


if __name__ == "__main__":
    unittest.main()
