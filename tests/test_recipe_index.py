import json
import tempfile
import unittest
from pathlib import Path

from src.recipe_index import load_recipe_index, lookup_recipe


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


if __name__ == "__main__":
    unittest.main()
