import json
import tempfile
import unittest
from pathlib import Path

from core.content_compiler import ContentCompiler, ContentCompilerError
from core.content_validation import ContentProjectValidator


class ContentCompilerTests(unittest.TestCase):
    def test_definition_validation_is_side_effect_free_and_reports_research_fields(self):
        definition = {
            "namespace": "demo", "name": "Validated Bed", "author": "Tester",
            "customization": {
                "layout": {"category": "Beds"},
                "model": {"source": "research-model"},
                "mechanics": {"comfort": 5},
            },
        }
        result = ContentCompiler.validate_definition(definition)
        self.assertTrue(result["valid"])
        self.assertEqual(result["research_only_fields"], ["mechanics", "model"])
        self.assertEqual(result["mechanics_preservation_policy"], "preserve")
        self.assertEqual(result["customization_matrix"]["model"]["runtime_action"], "hold_for_research")
        self.assertIn("placed-object model", result["customization_matrix"]["model"]["required_evidence"])
        self.assertEqual(result["deployment"], "compiler-only; no live game mutation")

    def test_compiles_definition_into_valid_research_project(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "SAFE_METADATA_RESOURCE_TYPES_20260928.json").write_text(json.dumps({
                "schema": "control_center.safe_metadata_resource_types.v1",
                "target_build": "test-build",
                "verified_types": [{"type": "keen::ItemInfo"}],
                "quarantined_types": [],
            }), encoding="utf-8")
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "Palm Beds", "id": "palm-bed", "name": "Palm Bed", "author": "Tester",
                "content_class": "item", "localization": {"palm_bed": {"en": "Palm Bed"}},
                "properties": {"itemId": 123},
            }, root / "project")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            content = json.loads((project / "content" / "content.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["feature_state"], "research-only")
            self.assertEqual(content["entries"][0]["name"], "Palm Bed")
            self.assertTrue(manifest["identity"]["guid"])
            self.assertEqual(content["entries"][0]["metadata_policy"]["state"], "verified")

    def test_rejects_incomplete_definition(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "profiles").mkdir(parents=True)
            with self.assertRaises(ContentCompilerError):
                ContentCompiler(base).compile({"namespace": "demo", "name": "Missing Author"}, Path(td) / "project")

    def test_metadata_policy_discovery_prefers_newest_dated_policy(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; research = base / "research"
            (base / "profiles").mkdir(parents=True); research.mkdir(parents=True)
            old = {"schema": "control_center.safe_metadata_resource_types.v1", "target_build": "old", "verified_types": [], "quarantined_types": []}
            new = {"schema": "control_center.safe_metadata_resource_types.v1", "target_build": "new", "verified_types": [{"type": "keen::ItemInfo"}], "quarantined_types": []}
            (research / "SAFE_METADATA_RESOURCE_TYPES_20260101.json").write_text(json.dumps(old), encoding="utf-8")
            (research / "SAFE_METADATA_RESOURCE_TYPES_20260928.json").write_text(json.dumps(new), encoding="utf-8")
            policy = ContentCompiler(base)._metadata_policy("keen::ItemInfo")
            self.assertEqual(policy["state"], "verified")
            self.assertEqual(policy["target_build"], "new")

    def test_compiler_can_include_a_png_icon(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            icon = root / "icon.png"; icon.write_bytes(b"\x89PNG\r\n\x1a\nicon")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "id": "icon-bed", "name": "Icon Bed", "author": "Tester",
                "definition_dir": str(root), "icon": "icon.png", "icon_slug": "icon-bed",
                "icon_resource_type": "keen::ItemInfo", "icon_field": "iconImage", "icon_resource_id": "3987654333",
            }, root / "project")
            assets = json.loads((project / "assets.json").read_text(encoding="utf-8"))
            self.assertEqual(assets["assets"][0]["id"], "demo:icon-bed")
            self.assertTrue((project / "assets" / "icons" / "icon.png").is_file())
            self.assertEqual(assets["references"][0]["field"], "iconImage")
            self.assertEqual(assets["references"][0]["resource_id"], "3987654333")

    def test_failed_icon_compile_removes_partial_new_project(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            icon = root / "bad.png"; icon.write_bytes(b"not png")
            destination = root / "project"
            with self.assertRaises(ContentCompilerError):
                ContentCompiler(base).compile({
                    "namespace": "demo", "name": "Broken", "author": "Tester",
                    "definition_dir": str(root), "icon": "bad.png",
                }, destination)
            self.assertFalse(destination.exists())
            self.assertFalse((base / "profiles" / "content-identities.json").exists())

    def test_compiler_records_customization_maturity_without_overclaiming_visual_edits(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "id": "custom-bed", "name": "Custom Bed", "author": "Tester",
                "localization": {"palm_bed": {"en": "Palm Bed"}},
                "customization": {
                    "layout": {"category": "Beds"},
                    "icon": {"source": "custom.png"},
                    "color": {"base": "#6b3f2a"},
                    "model": {"source": "other-bed"},
                },
            }, root / "project")
            content = json.loads((project / "content" / "content.json").read_text(encoding="utf-8"))
            contract = content["entries"][0]["customization"]
            self.assertEqual(contract["layout"]["status"], "verified")
            self.assertEqual(contract["icon"]["status"], "research-only")
            self.assertEqual(contract["icon"]["runtime_action"], "hold_for_research")
            self.assertEqual(contract["color"]["status"], "research-only")
            self.assertEqual(contract["model"]["runtime_action"], "hold_for_research")
            payload = (project / "src" / "localization_payload.lua").read_text(encoding="utf-8")
            self.assertIn('demo.palm_bed', payload)
            self.assertIn('"Palm Bed"', payload)

    def test_compiler_records_recipe_customization_plan_as_research_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Recipe Variant", "author": "Tester",
                "customization": {"recipe": {"ingredients": [{"item": 1, "amount": 2}], "station": "Carpenter"}},
            }, root / "project")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            plan = manifest["recipe_customization_plan"]
            self.assertEqual(plan["state"], "research-only")
            self.assertEqual(plan["runtime_action"], "hold_for_research")
            self.assertEqual(plan["requested_edits"]["ingredients"][0]["amount"], 2)

    def test_rejects_unknown_customization_field(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "profiles").mkdir(parents=True)
            with self.assertRaises(ContentCompilerError):
                ContentCompiler(base).compile({
                    "namespace": "demo", "name": "Bad", "author": "Tester",
                    "customization": {"teleport_mesh": True},
                }, Path(td) / "project")

    def test_rejects_malformed_recipe_customization_values(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "profiles").mkdir(parents=True)
            with self.assertRaises(ContentCompilerError):
                ContentCompiler(base).compile({
                    "namespace": "demo", "name": "Bad Recipe", "author": "Tester",
                    "customization": {"recipe": {"ingredients": [{"item": 0, "amount": 2}]}},
                }, Path(td) / "project")
            with self.assertRaises(ContentCompilerError):
                ContentCompiler(base).compile({
                    "namespace": "demo", "name": "Bad Recipe", "author": "Tester",
                    "customization": {"recipe": {"craftingDuration": -1}},
                }, Path(td) / "project2")

    def test_rejects_non_object_recipe_customization(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "profiles").mkdir(parents=True)
            with self.assertRaises(ContentCompilerError):
                ContentCompiler(base).compile({
                    "namespace": "demo", "name": "Bad Recipe", "author": "Tester",
                    "customization": {"recipe": ["not-an-object"]},
                }, Path(td) / "project")

    def test_mechanics_customization_defaults_to_donor_preservation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Preserved Bed", "author": "Tester",
                "customization": {"mechanics": {"comfort": 5}},
            }, root / "project")
            content = json.loads((project / "content" / "content.json").read_text(encoding="utf-8"))
            mechanics = content["entries"][0]["customization"]["mechanics"]
            self.assertEqual(mechanics["requested"]["preservation_policy"], "preserve")
            self.assertEqual(mechanics["status"], "research-only")
            self.assertEqual(mechanics["runtime_action"], "hold_for_research")

    def test_rejects_unknown_mechanics_preservation_policy(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "profiles").mkdir(parents=True)
            identity = base / "profiles" / "content-identities.json"
            with self.assertRaisesRegex(ContentCompilerError, "preservation_policy"):
                ContentCompiler(base).compile({
                    "namespace": "demo", "name": "Bad Mechanics", "author": "Tester",
                    "customization": {"mechanics": {"preservation_policy": "guess"}},
                }, Path(td) / "project")
            self.assertFalse((Path(td) / "project").exists())
            self.assertFalse(identity.exists())

    def test_rejects_unknown_mechanics_field(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "profiles").mkdir(parents=True)
            with self.assertRaisesRegex(ContentCompilerError, "Unsupported mechanics customization fields"):
                ContentCompiler(base).compile({
                    "namespace": "demo", "name": "Bad Mechanics Field", "author": "Tester",
                    "customization": {"mechanics": {"teleport": True}},
                }, Path(td) / "project")

    def test_emits_research_gated_mechanics_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Mechanics Variant", "author": "Tester",
                "customization": {"mechanics": {"comfort": 5, "preservation_policy": "replace"}},
            }, root / "project")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            plan = manifest["mechanics_customization_plan"]
            self.assertEqual(plan["schema"], "control_center.mechanics_customization_plan.v1")
            self.assertEqual(plan["state"], "research-only")
            self.assertEqual(plan["preservation_policy"], "replace")

    def test_compiler_emits_runtime_lua_for_item_clone_definition(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Runtime Bed", "author": "Tester",
                "resource_type": "keen::ItemInfo", "donor_id": 2940001508, "new_item_id": 3987654333,
                "donor_recipe_id": 3531872774, "new_recipe_id": 3987654334,
            }, root / "project")
            source = (project / "src" / "mod.lua").read_text(encoding="utf-8")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            self.assertIn("kfc.clone_recipe_set(ui, 3531872774, 3987654334)", source)
            self.assertTrue(manifest["runtime_generation"]["recipe_linkage"])
            self.assertEqual(manifest["recipe_ui_plan"]["fixed_array_policy"],
                             "clone_set_replace_typed_entry")

    def test_compiler_records_asset_substitution_plan_as_research_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Visual Bed", "author": "Tester",
                "donor_id": 2940001508, "new_item_id": 3987654402,
                "asset_substitutions": [{"field": "visualModel", "resource_guid": "model-guid"}],
            }, root / "project")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["asset_substitution_plan"]["state"], "research-only")
            self.assertTrue(manifest["asset_substitution_plan"]["requires_resource_graph_validation"])
            self.assertEqual(manifest["asset_dependencies"], ["model-guid"])

    def test_compiler_emits_visual_variant_contract_with_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Variant Bed", "author": "Tester",
                "donor_id": 2940001508, "new_item_id": 3987654403,
                "compatible_game_build": "1076226",
                "asset_substitutions": [{"field": "visualModel", "resource_guid": "model-guid", "resource_type": "keen::RenderModel"}],
                "customization": {"model": {"source": "model-guid"}, "color": {"tint": "#884422"}},
            }, root / "project")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            plan = manifest["visual_variant_plan"]
            self.assertEqual(plan["state"], "research-only")
            self.assertEqual(plan["fallback"], "preserve_donor_visual_and_mechanics")
            self.assertEqual(plan["compatibility"]["required_resource_types"], ["keen::RenderModel"])

    def test_compiler_carries_color_adjustment_into_asset_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Color Variant", "author": "Tester",
                "donor_id": 1, "new_item_id": 2,
                "asset_substitutions": [{"field": "visualModel", "resource_guid": "model-guid"}],
                "customization": {"color": {"target": "frame", "tint": "#884422"}},
            }, root / "project")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["asset_substitution_plan"]["color_adjustments"],
                             [{"target": "frame", "color": "#884422"}])

    def test_compiler_normalizes_texture_shorthand_into_asset_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Texture Variant", "author": "Tester",
                "donor_id": 1, "new_item_id": 2,
                "asset_substitutions": [],
                "customization": {"texture": {"resource_guid": "texture-guid", "resource_type": "keen::TextureResource"}},
            }, root / "project")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["asset_substitution_plan"]["substitutions"][0]["field"], "texture")
            self.assertEqual(manifest["asset_dependencies"], ["texture-guid"])

    def test_compiler_normalizes_visual_shorthand_without_explicit_asset_array(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Shorthand Variant", "author": "Tester",
                "donor_id": 1, "new_item_id": 2,
                "customization": {
                    "model": {"resource_guid": "model-guid", "resource_type": "keen::RenderModel"},
                    "color": {"tint": "#884422"},
                },
            }, root / "project")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            plan = manifest["asset_substitution_plan"]
            self.assertEqual(plan["substitutions"][0]["field"], "visualModel")
            self.assertEqual(plan["substitutions"][0]["resource_guid"], "model-guid")
            self.assertEqual(plan["color_adjustments"], [{"target": "material", "color": "#884422"}])

    def test_compiler_accepts_visual_variant_template_shape(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            for name in ("kfc_content_registry.lua", "kfc_localization_registry.lua"):
                (base / "research" / "runtime" / name).write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Template Variant", "author": "Tester",
                "donor_id": 1, "new_item_id": 2,
                "visual_variant": {
                    "replacement_model_guid": "model-guid",
                    "materials": [], "textures": [],
                    "color_adjustments": [{"target": "frame", "color": "#123456"}],
                    "scale": [1.2, 1.0, 0.8], "offset": [0.0, 0.1, 0.0],
                    "catalog_preview": "custom-research", "placement_preview": "custom-research",
                },
            }, root / "project")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["asset_substitution_plan"]["substitutions"][0]["field"], "visualModel")
            self.assertEqual(manifest["asset_substitution_plan"]["color_adjustments"], [{"target": "frame", "color": "#123456"}])
            self.assertEqual(manifest["visual_variant_plan"]["requested_visual_changes"]["visual_transform"]["scale"], [1.2, 1.0, 0.8])
            self.assertEqual(manifest["visual_variant_plan"]["catalog_preview_policy"], "custom-research")

    def test_compiler_preserves_packed_item_color_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            for name in ("kfc_content_registry.lua", "kfc_localization_registry.lua"):
                (base / "research" / "runtime" / name).write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Packed Colors", "author": "Tester",
                "donor_id": 1, "new_item_id": 2,
                "customization": {"item_color_combination": {
                    "runtime_field": "itemColorCombinationSetup", "color0": 1,
                    "color1": 2, "color2": 3, "isSet": True,
                }},
            }, root / "project")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["visual_variant_plan"]["requested_visual_changes"]["item_color_combination"]["color1"], 2)

    def test_compiler_rejects_malformed_visual_transform(self):
        with self.assertRaises(ContentCompilerError):
            ContentCompiler.validate_definition({
                "namespace": "demo", "name": "Bad Transform", "author": "Tester",
                "customization": {"visual_transform": {"scale": [1.0, 2.0]}},
            })

    def test_compiler_rejects_invalid_packed_color_plan(self):
        with self.assertRaisesRegex(ContentCompilerError, "packed 32-bit"):
            ContentCompiler.validate_definition({
                "namespace": "demo", "name": "Bad Colors", "author": "Tester",
                "customization": {"item_color_combination": {
                    "runtime_field": "itemColorCombinationSetup", "color0": "red",
                    "color1": 2, "color2": 3, "isSet": True,
                }},
            })

    def test_compiler_imports_declared_project_assets(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            model = root / "bed.gltf"
            model.write_text('{"asset":{"version":"2.0"}}', encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Imported Bed", "author": "Tester",
                "definition_dir": str(root),
                "assets": [{"source": "bed.gltf", "kind": "models", "name": "bed.gltf"}],
            }, root / "project")
            self.assertTrue((project / "assets" / "models" / "bed.gltf").is_file())
            self.assertEqual(ContentProjectValidator().validate(project).valid, True)

    def test_definition_rejects_malformed_asset_provenance_before_compile(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "profiles").mkdir(parents=True)
            with self.assertRaisesRegex(ContentCompilerError, "Unsupported asset provenance fields"):
                ContentCompiler(base).compile({
                    "namespace": "demo", "name": "Bad Provenance", "author": "Tester",
                    "assets": [{"source": "chair.gltf", "kind": "models", "provenance": {"owner": "x"}}],
                }, Path(td) / "project")

    def test_compiler_generates_read_only_visual_probe(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Visual Probe", "author": "Tester",
                "visual_probe": True, "visual_resource_type": "keen::RenderModel",
                "asset_dependencies": ["model-guid"],
            }, root / "project")
            source = (project / "src" / "mod.lua").read_text(encoding="utf-8")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            self.assertIn("read_only_no_visual_mutation", source)
            self.assertTrue(manifest["runtime_generation"]["read_only"])

    def test_compiler_stages_template_model_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); base = root / "control"
            (base / "profiles").mkdir(parents=True)
            (base / "research" / "runtime").mkdir(parents=True)
            (base / "research" / "runtime" / "kfc_content_registry.lua").write_text("return {}", encoding="utf-8")
            (base / "research" / "runtime" / "kfc_localization_registry.lua").write_text("return {}", encoding="utf-8")
            template = root / "template.json"
            template.write_text('{"components":[{"$type":"keen::ecs::ModelResource","$value":{"model":"donor"}}]}', encoding="utf-8")
            project = ContentCompiler(base).compile({
                "namespace": "demo", "name": "Template Variant", "author": "Tester",
                "definition_dir": str(root), "template_model_source": "template.json",
                "template_model_replacement_guid": "replacement",
            }, root / "project")
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            candidate = project / manifest["template_graph_plan"]["candidate_path"]
            self.assertEqual(json.loads(candidate.read_text())["components"][0]["$value"]["model"], "replacement")
            self.assertEqual(len(manifest["template_graph_plan"]["candidate_sha256"]), 64)
            self.assertEqual(manifest["template_graph_plan"]["component_inventory"][0]["type"], "keen::ecs::ModelResource")


if __name__ == "__main__":
    unittest.main()
