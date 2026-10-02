import json
import tempfile
import unittest
from pathlib import Path

from core.content_classes import ContentClassService
from core.content_validation import ContentProjectValidator


class ContentClassTests(unittest.TestCase):
    def test_bed_schema_infers_verified_profile(self):
        profile = ContentClassService().infer({"schema": "control_center.bed_clone_staging.v1"})
        self.assertEqual(profile.status, "verified")
        self.assertIn("FbUiBundle", profile.required_resource_types)

    def test_missing_verified_family_is_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "content.json").write_text(json.dumps({
                "id": "demo", "name": "Demo", "version": "1.0.0", "content_class": "furniture_bed"
            }), encoding="utf-8")
            (root / "ItemInfo").mkdir()
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any(i.code == "content_class.resource_missing" for i in report.issues))

    def test_research_class_warns_without_blocking(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "content.json").write_text(json.dumps({
                "id": "demo", "name": "Demo", "version": "1.0.0", "content_class": "recipe"
            }), encoding="utf-8")
            (root / "RecipeRegistryResource").mkdir()
            report = ContentProjectValidator().validate(root)
            self.assertTrue(report.valid)
            self.assertTrue(any(i.code == "content_class.research_only" for i in report.issues))

    def test_donor_schema_requires_furniture_identity_and_ui_link(self):
        profile = ContentClassService().profile("furniture_bed")
        issues = ContentClassService().validate_donor_schema(profile, {"guid": "donor-guid", "item_id": 10})
        self.assertTrue(any("recipe_id" in issue for issue in issues))
        self.assertTrue(any("UI recipe link" in issue for issue in issues))

    def test_donor_schema_accepts_complete_furniture_profile(self):
        profile = ContentClassService().profile("furniture_bed")
        issues = ContentClassService().validate_donor_schema(profile, {
            "guid": "donor-guid", "item_id": 10, "recipe_id": 20, "ui_recipe_link": 20,
        })
        self.assertEqual(issues, [])

    def test_project_validation_enforces_declared_donor_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "content.json").write_text(json.dumps({
                "id": "demo", "name": "Demo", "version": "1.0.0",
                "content_class": "furniture_bed",
                "donor_metadata": {"guid": "donor-guid", "item_id": 10},
            }), encoding="utf-8")
            for folder in ("ItemInfo", "ItemRegistryResource", "RecipeRegistryResource", "ItemKnowledgeResource", "FbUiBundle"):
                (root / folder).mkdir()
                (root / folder / "resource.json").write_text("{}", encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertTrue(any(issue.code == "donor_schema.identity" for issue in report.issues))


if __name__ == "__main__":
    unittest.main()
