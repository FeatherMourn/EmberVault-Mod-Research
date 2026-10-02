import json
import unittest
from pathlib import Path

from core.content_validation import ContentProjectValidator
from core.resource_inspector import ResourceInspector


class VerifiedBedFixtureTests(unittest.TestCase):
    ROOT = Path(r"I:\My Drive\Enshrouded Mods\Control_Center\research\staging\bed_clone_kfc_subset_1076226")

    def test_live_bed_fixture_identity_and_safety_contract(self):
        manifest = json.loads((self.ROOT / "CLONE_MANIFEST.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(manifest["schema"], "control_center.bed_clone_staging.v1")
        self.assertEqual(manifest["donorItemId"], 2940001508)
        self.assertEqual(manifest["cloneItemId"], 3987654321)
        self.assertEqual(manifest["donorRecipeId"], 3531872774)
        self.assertEqual(manifest["cloneRecipeId"], 3987654322)
        self.assertFalse(manifest["liveGameModified"])

    def test_fixture_contains_the_runtime_resource_families(self):
        report = ContentProjectValidator().validate(self.ROOT)
        self.assertTrue(report.valid, [issue.message for issue in report.issues])
        records = ResourceInspector().scan(self.ROOT)
        types = {record.resource_type for record in records}
        for required in ("ItemInfo", "ItemRegistryResource", "RecipeRegistryResource", "ItemKnowledgeResource", "FbUiBundle"):
            self.assertIn(required, types)


if __name__ == "__main__":
    unittest.main()
