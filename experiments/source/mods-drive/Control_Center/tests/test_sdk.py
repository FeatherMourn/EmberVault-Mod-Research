import tempfile
import unittest
from pathlib import Path

from core.sdk import DeveloperSdk


class SdkTests(unittest.TestCase):
    def test_sdk_manifest_and_helper_packaging(self):
        base = Path(__file__).parents[1]
        sdk = DeveloperSdk(base)
        self.assertEqual(sdk.manifest()["schema"], "control_center.sdk.v1")
        self.assertIn("kfc.localization_registry", sdk.manifest()["capabilities"])
        with tempfile.TemporaryDirectory() as td:
            destination = sdk.package_helper(Path(td) / "module")
            self.assertTrue(destination.is_file())
            self.assertIn("register_resource", destination.read_text(encoding="utf-8"))
            self.assertIn("function M.edit_recipe", destination.read_text(encoding="utf-8"))
            self.assertIn("function M.clone_recipe_for_edit", destination.read_text(encoding="utf-8"))
            self.assertIn("function M.replace_knowledge_requirement", destination.read_text(encoding="utf-8"))
            localization = destination.parent / "kfc_localization_registry.lua"
            self.assertTrue(localization.is_file())
            self.assertIn("LocaTagCollectionResourceData", localization.read_text(encoding="utf-8"))
            self.assertIn("register_tag", localization.read_text(encoding="utf-8"))
            self.assertIn("locale_filter", localization.read_text(encoding="utf-8"))
            self.assertIn("Older EML builds", localization.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
