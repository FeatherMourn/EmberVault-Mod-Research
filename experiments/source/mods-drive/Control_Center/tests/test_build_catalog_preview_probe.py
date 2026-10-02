import json
import tempfile
import unittest
from pathlib import Path

from tools.build_catalog_preview_probe import build


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "research" / "probes" / "recipe_customization_workshop_20260928"


class CatalogPreviewProbeGeneratorTests(unittest.TestCase):
    def test_generates_research_only_image_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "catalog_preview_image_only_20260928"
            manifest = build(TEMPLATE, output, new_item_id=3987654821, new_recipe_id=3987654822)
            saved = json.loads((output / "mod.json").read_text(encoding="utf-8"))
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertEqual(manifest, saved)
            self.assertEqual(saved["candidate_id"], "image_only_donor_preview")
            self.assertEqual(saved["feature_state"], "research-only")
            self.assertFalse(saved["stable_profile_allowed"])
            self.assertIn("assign_catalog_icon", source)
            self.assertIn("CATALOG_PREVIEW_AFTER", source)
            self.assertNotIn("3987654809", source)
            self.assertIn("3987654821", source)
            self.assertIn("3987654822", source)

    def test_rejects_existing_output(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "existing"
            output.mkdir()
            with self.assertRaises(ValueError):
                build(TEMPLATE, output, new_item_id=1, new_recipe_id=2)

    def test_accepts_fixture_with_different_identity_markers(self):
        with tempfile.TemporaryDirectory() as td:
            template = Path(td) / "template"
            (template / "src").mkdir(parents=True)
            (template / "src" / "mod.lua").write_text(
                "local NEW_ITEM_ID = 123456789\n"
                "local NEW_RECIPE_ID = 987654321\n"
                "clone.data.objectId = clone.guid\n",
                encoding="utf-8",
            )
            output = Path(td) / "probe"
            build(template, output, new_item_id=10, new_recipe_id=11)
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertIn("local NEW_ITEM_ID = 10", source)
            self.assertIn("local NEW_RECIPE_ID = 11", source)

    def test_rejects_native_out_of_range_ids(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "32-bit"):
                build(TEMPLATE, Path(td) / "probe", new_item_id=0x1_0000_0000, new_recipe_id=3987654822)

    def test_generates_cleared_fallback_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "catalog_preview_cleared_fallbacks"
            manifest = build(TEMPLATE, output, new_item_id=3987654831,
                             new_recipe_id=3987654832, clear_icon_fallbacks=True)
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertEqual(manifest["candidate_id"], "image_only_cleared_fallbacks")
            self.assertIn("clone.data.iconModel = ZERO_GUID", source)
            self.assertIn("clone.data.iconScene = ZERO_GUID", source)
            self.assertEqual(manifest["mutates"], ["iconImage", "iconModel", "iconScene"])

    def test_generates_single_render_control_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "catalog_preview_render_scale"
            manifest = build(TEMPLATE, output, new_item_id=3987654841,
                             new_recipe_id=3987654842,
                             render_control="iconRenderGlobalScale")
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertEqual(manifest["candidate_id"], "render_control_iconRenderGlobalScale")
            self.assertIn("field=iconRenderGlobalScale", source)
            self.assertIn("CATALOG_RENDER_CONTROL", source)
            self.assertEqual(manifest["mutates"], ["iconImage", "iconRenderGlobalScale"])

    def test_generates_structured_offset_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "catalog_preview_offset"
            manifest = build(TEMPLATE, output, new_item_id=3987654851,
                             new_recipe_id=3987654852,
                             render_control="iconRenderOffset")
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertEqual(manifest["candidate_id"], "render_control_iconRenderOffset")
            self.assertIn("localOffset = { x = 0.1", source)

    def test_generates_item_color_combination_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "catalog_preview_item_colors"
            manifest = build(TEMPLATE, output, new_item_id=3987654861,
                             new_recipe_id=3987654862,
                             render_control="itemColorCombinationSetup")
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertEqual(manifest["candidate_id"],
                             "render_control_itemColorCombinationSetup")
            self.assertIn("color0 = { 180, 60, 60, 255 }", source)
            self.assertIn("isSet = true", source)
            self.assertEqual(manifest["mutates"],
                             ["iconImage", "itemColorCombinationSetup"])

    def test_generates_packed_item_color_combination_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "catalog_preview_item_colors_packed"
            manifest = build(TEMPLATE, output, new_item_id=3987654871,
                             new_recipe_id=3987654872,
                             render_control="itemColorCombinationPacked")
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertIn("field=itemColorCombinationPacked", source)
            self.assertIn("color0 = 0xFF3C3CB4", source)
            self.assertEqual(manifest["mutates"],
                             ["iconImage", "itemColorCombinationPacked"])

    def test_accepts_project_packed_colors(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "catalog_preview_project_colors"
            manifest = build(TEMPLATE, output, new_item_id=3987654881,
                             new_recipe_id=3987654882,
                             render_control="itemColorCombinationPacked",
                             packed_colors=(1, 2, 0xFFFFFFFF))
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertIn("color0 = 0x00000001", source)
            self.assertIn("color2 = 0xFFFFFFFF", source)
            self.assertEqual(manifest["packed_colors"], [1, 2, 0xFFFFFFFF])

    def test_loads_packed_colors_from_visual_variant(self):
        with tempfile.TemporaryDirectory() as td:
            definition = Path(td) / "visual_variant.json"
            definition.write_text(json.dumps({"item_color_combination": {
                "runtime_field": "itemColorCombinationSetup", "color0": 11,
                "color1": 22, "color2": 33, "isSet": True,
            }}), encoding="utf-8")
            from tools.build_catalog_preview_probe import load_packed_colors
            self.assertEqual(load_packed_colors(definition), (11, 22, 33))


if __name__ == "__main__":
    unittest.main()
