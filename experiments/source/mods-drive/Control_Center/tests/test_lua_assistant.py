import tempfile
import unittest
from pathlib import Path

from core.lua_assistant import LuaAssistant


class LuaAssistantTests(unittest.TestCase):
    def test_generates_research_gated_lua(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td) / "mod.lua"
            source = LuaAssistant().generate({"id": "palm-bed", "resource_type": "keen::ItemInfo", "donor_id": 123}, destination)
            self.assertIn("research-only", source)
            self.assertIn("DONOR_ID = 123", source)
            self.assertTrue(destination.is_file())

    def test_manifest_snippet_declares_capability(self):
        manifest = LuaAssistant.manifest_snippet({})
        self.assertEqual(manifest["required_loader_api"], "assets.register_resource")
        self.assertEqual(manifest["feature_state"], "research-only")

    def test_generated_customization_is_gated_and_research_edits_are_not_applied(self):
        source = LuaAssistant().generate({
            "id": "custom-bed", "donor_id": 123, "new_item_id": 456,
            "customization": {"identity": {"debugName": "Palm Bed"}, "model": {"source": "new-mesh"}},
        })
        self.assertIn('clone.data["debugName"] = "Palm Bed"', source)
        self.assertIn("RESEARCH-ONLY: model customization", source)

    def test_generated_icon_customization_is_gated_until_visual_evidence(self):
        source = LuaAssistant().generate({
            "id": "icon-bed",
            "resource_type": "keen::ItemInfo",
            "donor_id": 2940001508,
            "new_item_id": 3987654402,
            "customization": {"icon": {"iconImage": "new-icon-guid"}},
        })
        self.assertIn("RESEARCH-ONLY: icon customization", source)
        self.assertNotIn('clone.data["iconImage"]', source)

    def test_localization_probe_uses_compiled_payload_and_is_explicit(self):
        source = LuaAssistant().generate_localization_probe("locale-guid", "loc")
        self.assertIn("require, 'kfc_localization_registry'", source)
        self.assertIn("require, 'localization_payload'", source)
        self.assertIn("research_only_localization_registration", source)

    def test_localization_helper_uses_compatible_hasher_fallback(self):
        helper = Path("research/runtime/kfc_localization_registry.lua").read_text(encoding="utf-8")
        self.assertIn("rawget(_G, 'hasher')", helper)
        self.assertIn("hash = 2166136261", helper)

    def test_content_helper_classifies_missing_metadata_api(self):
        helper = Path("research/runtime/kfc_content_registry.lua").read_text(encoding="utf-8")
        self.assertIn("resource_metadata_by_type", helper)
        self.assertIn("metadata_api_unavailable", helper)
        self.assertIn("type_quarantined", helper)
        self.assertIn("keen::TemplateResource", helper)

    def test_content_helper_reads_mapped_variants_safely(self):
        helper = Path("research/runtime/kfc_content_registry.lua").read_text(encoding="utf-8")
        self.assertIn("read_mapped_variant", helper)
        self.assertIn("try_pairs", helper)
        self.assertIn("pairs_failed:", helper)

    def test_content_helper_exposes_gated_png_recolor_route(self):
        helper = Path("research/runtime/kfc_content_registry.lua").read_text(encoding="utf-8")
        self.assertIn("import_recolored_png_icon", helper)
        self.assertIn("decoded:set_pixel", helper)
        self.assertIn("mutate a vanilla texture", helper)

    def test_content_helper_supports_explicit_complex_resource_identity(self):
        helper = Path("research/runtime/kfc_content_registry.lua").read_text(encoding="utf-8")
        self.assertIn("explicit_guid", helper)
        self.assertIn("resource_registration_failed:", helper)
        self.assertIn("part_must_be_number", helper)

    def test_item_definition_generates_real_donor_clone_route(self):
        source = LuaAssistant().generate({"id": "bed", "resource_type": "keen::ItemInfo",
                                          "donor_id": 123, "new_item_id": 456})
        self.assertIn("game.assets.get_resources_by_type", source)
        self.assertIn("local donor", source)
        self.assertIn("clone.data.itemId.value = 456", source)
        self.assertNotIn('log("DONOR_CANDIDATE"', source)

    def test_item_definition_can_generate_recipe_and_ui_linkage(self):
        source = LuaAssistant().generate({"id": "bed", "resource_type": "keen::ItemInfo",
                                          "donor_id": 123, "new_item_id": 456,
                                          "donor_recipe_id": 789, "new_recipe_id": 987})
        self.assertIn("item_registry", source)
        self.assertIn("candidate.data and candidate.data.itemRefs", source)
        self.assertIn("clone.data.objectId = clone.guid", source)
        self.assertIn("recipe.recipeId.value = 987", source)
        self.assertIn("kfc.clone_recipe_set(ui, 789, 987)", source)

    def test_generated_recipe_lookup_matches_recipe_id_or_donor_output(self):
        source = LuaAssistant().generate({
            "id": "bed", "resource_type": "keen::ItemInfo",
            "donor_id": 123, "new_item_id": 456,
            "donor_recipe_id": 789, "new_recipe_id": 987,
        })
        self.assertIn("recipe.recipeId.value == 789", source)
        self.assertIn("output.item.value == 123", source)
        self.assertIn("keen::ds::RecipeRegistryResource", source)

    def test_minimal_probe_is_small_and_validated(self):
        source = LuaAssistant().generate_minimal_clone_probe(
            "01474f79-6b5a-4bcd-999d-7e9339fda91c", 3987654369, "probe-v21"
        )
        self.assertIn("CC-MINIMAL-CLONE:probe-v21", source)
        self.assertIn("game.assets.register_resource(donor.data, 'keen::ItemInfo')", source)
        self.assertIn("CLONED_ITEM", source)
        with self.assertRaises(ValueError):
            LuaAssistant().generate_minimal_clone_probe("", 1)

    def test_registry_probe_checks_index_growth(self):
        source = LuaAssistant().generate_registry_clone_probe("guid", 456, "registry-v1")
        self.assertIn("CC-REGISTRY-CLONE:registry-v1", source)
        self.assertIn("table.insert(registry.data.itemRefs, result)", source)
        self.assertIn("result.data.objectId = result.guid", source)
        self.assertIn("if candidate and candidate.data and candidate.data.itemRefs", source)
        self.assertIn("table.insert(registry.data.dbgNames, result.data.debugName)", source)
        self.assertIn("INDEX_LOOKUP", source)
        self.assertIn("local before = #registry.data.itemRefs", source)
        self.assertIn("local entry_data = entry and entry.data or entry", source)
        self.assertIn("ENTRY_SHAPE", source)
        self.assertIn("FIRST_SHAPE", source)
        self.assertIn("INDEXED_ITEM", source)

    def test_visual_substitution_probe_is_read_only_and_tracks_dependencies(self):
        source = LuaAssistant().generate_visual_substitution_probe(
            "keen::RenderModel", ["model-guid", "material-guid"], "visual-v1"
        )
        self.assertIn("CC-VISUAL-PROBE:visual-v1", source)
        self.assertIn("model-guid", source)
        self.assertIn("read_only_no_visual_mutation", source)

    def test_visual_field_probe_is_read_only(self):
        source = LuaAssistant().generate_visual_field_probe("donor-guid", "fields-v1")
        self.assertIn("CC-VISUAL-FIELDS:fields-v1", source)
        self.assertIn('"visualModel"', source)
        self.assertIn("read_only_field_inventory", source)

    def test_resource_graph_probe_tracks_guid_type_matches(self):
        source = LuaAssistant().generate_resource_graph_probe(
            ["model-guid"], ["keen::RenderModel"], "graph-v1"
        )
        self.assertIn("CC-RESOURCE-GRAPH:graph-v1", source)
        self.assertIn("MATCH", source)
        self.assertIn("read_only_resource_graph", source)

    def test_single_resource_probe_is_minimal(self):
        source = LuaAssistant().generate_single_resource_probe(
            "keen::RenderModel", "model-guid", "single-v1"
        )
        self.assertIn("CC-SINGLE-RESOURCE:single-v1", source)
        self.assertIn("read_only_single_lookup", source)
        self.assertNotIn("TYPES =", source)

    def test_metadata_probe_handles_undecodable_resources(self):
        source = LuaAssistant().generate_resource_metadata_probe(
            "keen::TemplateResource", "template-guid", "metadata-v1"
        )
        self.assertIn("CC-RESOURCE-METADATA:metadata-v1", source)
        self.assertIn("get_resource_metadata_by_type", source)
        self.assertIn("read_only_metadata_identity", source)
        self.assertIn('log("API"', source)
        self.assertIn('type(game.assets and game.assets.get_resource_metadata_by_type)', source)

    def test_single_metadata_probe_is_bounded(self):
        source = LuaAssistant().generate_resource_metadata_single_probe(
            "keen::TemplateResource", "template-guid", "single-v1"
        )
        self.assertIn("get_resource_metadata(WANTED_GUID, TYPE_NAME, 0)", source)
        self.assertIn("BEFORE_CALL", source)
        self.assertIn("AFTER_CALL", source)
        self.assertNotIn("get_resource_metadata_by_type", source)

    def test_blueprint_payload_probe_is_bounded_and_read_only(self):
        source = LuaAssistant().generate_blueprint_registry_payload_probe(
            "registry-guid", "blueprint-v1"
        )
        self.assertIn("CC-BLUEPRINT-PAYLOAD:blueprint-v1", source)
        self.assertIn("blueprintItems", source)
        self.assertIn("read_only=true|bounded=true", source)
        self.assertIn("created=false|registered=false|mutated=false", source)
        self.assertNotIn("__newindex", source)

    def test_item_visual_reference_probe_is_clone_only(self):
        source = LuaAssistant().generate_item_visual_reference_probe(
            "donor-guid", 123, "replacement-guid", "visual-ref-v1"
        )
        self.assertIn("CC-ITEM-VISUAL:visual-ref-v1", source)
        self.assertIn("clone_only_no_registry_mutation", source)


if __name__ == "__main__":
    unittest.main()
