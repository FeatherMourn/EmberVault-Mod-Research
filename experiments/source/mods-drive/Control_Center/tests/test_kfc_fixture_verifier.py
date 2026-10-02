import json
import tempfile
import unittest
from pathlib import Path

from research.tools.verify_kfc_fixture import verify


class KfcFixtureVerifierTests(unittest.TestCase):
    def test_complete_fixture_is_distinguished_from_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payloads = {
                "ItemInfo/item.json": "3987654321 CC_Custom_Bed_001",
                "ItemRegistryResource/registry.json": "CC_Custom_Bed_001",
                "RecipeRegistryResource/recipes.json": "3987654322 3987654321 b3c6d8a1-2e47-5f90-8c13-7a6b4d9e2051",
                "ItemKnowledgeResource/knowledge.json": "3987654321",
                "FbUiBundle/ui.json": "3987654322",
            }
            for relative, text in payloads.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")

            report = verify(
                root,
                3987654321,
                3987654322,
                "CC_Custom_Bed_001",
                "b3c6d8a1-2e47-5f90-8c13-7a6b4d9e2051",
            )

        self.assertTrue(report["archive_registration_complete"])
        self.assertFalse(report["client_rendering_verified"])
        self.assertTrue(report["checks"]["recipe_guid"])

    def test_recipe_guid_prevents_donor_identity_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "RecipeRegistryResource/recipes.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("3987654322 3987654321 donor-guid", encoding="utf-8")

            report = verify(
                root,
                3987654321,
                3987654322,
                "CC_Custom_Bed_001",
                "unique-guid",
            )

        self.assertFalse(report["checks"]["recipe_guid"])
        self.assertFalse(report["archive_registration_complete"])


if __name__ == "__main__":
    unittest.main()
