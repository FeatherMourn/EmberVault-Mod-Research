import json
import tempfile
import unittest
from pathlib import Path

from tools.find_ui_preview_fields import search


class UiPreviewFieldTests(unittest.TestCase):
    def test_finds_nested_preview_fields_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(json.dumps({"families": [{"fields": [{"name": "iconImage"}, {"name": "show_picker_preview"}, {"name": "iconImage"}]}]}), encoding="utf-8")
            result = search(path)
        self.assertEqual(result["schema"], "control_center.ui_preview_field_candidates.v1")
        self.assertEqual(result["candidate_count"], 2)
        self.assertEqual({item["field"] for item in result["candidates"]}, {"iconImage", "show_picker_preview"})

    def test_family_filter_excludes_unrelated_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(json.dumps({"families": [
                {"family": "FbUiBundle", "fields": [{"name": "icons"}]},
                {"family": "ItemInfo", "fields": [{"name": "iconImage"}]},
            ]}), encoding="utf-8")
            result = search(path, "FbUiBundle")
        self.assertEqual({item["field"] for item in result["candidates"]}, {"icons"})

    def test_reflected_type_filter_selects_one_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(json.dumps({"families": [{"family": "FbUiBundle", "reflected_types": [
                {"name": "keen::FbUiBundle", "fields": [{"name": "iconImage"}]},
                {"name": "keen::ds::FbUiBundle", "fields": [{"name": "icons"}]},
            ]}]}), encoding="utf-8")
            result = search(path, "FbUiBundle", "keen::FbUiBundle")
        self.assertEqual({item["field"] for item in result["candidates"]}, {"iconImage"})


if __name__ == "__main__":
    unittest.main()
