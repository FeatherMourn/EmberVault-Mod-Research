import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.research_lab import ResearchProbeService


class ResearchLabTests(unittest.TestCase):
    def test_controlled_validation_preflight_fails_closed_for_running_or_missing_session(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); game = root / "game"; probe = root / "probe"; (game / "logs").mkdir(parents=True); (probe / "src").mkdir(parents=True)
            (game / "Enshrouded.exe").write_bytes(b"placeholder")
            (probe / "mod.json").write_text('{"research_build":"1076226"}', encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            with patch("core.research_lab.subprocess.check_output", return_value="enshrouded.exe"):
                report = ResearchProbeService.controlled_validation_preflight(game, probe, "1076226")
            self.assertFalse(report["ready"])
            self.assertTrue(any("currently running" in issue for issue in report["issues"]))

    def test_controlled_validation_preflight_checks_declared_dependencies(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); game = root / "game"; probe = root / "probe"; (game / "logs").mkdir(parents=True); (probe / "src").mkdir(parents=True)
            (game / "Enshrouded.exe").write_bytes(b"placeholder")
            (probe / "mod.json").write_text('{"research_build":"1076226","dependencies":[{"id":"donor"}]}', encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            with patch("core.research_lab.subprocess.check_output", return_value=""):
                report = ResearchProbeService.controlled_validation_preflight(game, probe, "1076226")
            self.assertFalse(report["ready"])
            self.assertTrue(any("Required dependency" in issue for issue in report["issues"]))

    def test_controlled_validation_preflight_checks_dependency_versions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); game = root / "game"; probe = root / "probe"; (game / "logs").mkdir(parents=True); (probe / "src").mkdir(parents=True); (game / "mods" / "donor").mkdir(parents=True)
            (game / "Enshrouded.exe").write_bytes(b"placeholder")
            (game / "mods" / "donor" / "mod.json").write_text('{"version":"0.1.0"}', encoding="utf-8")
            (probe / "mod.json").write_text('{"research_build":"1076226","dependencies":[{"id":"donor","version":">=1.0.0"}]}', encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            with patch("core.research_lab.subprocess.check_output", return_value=""):
                report = ResearchProbeService.controlled_validation_preflight(game, probe, "1076226")
            self.assertFalse(report["ready"])
            self.assertTrue(any("incompatible version" in issue for issue in report["issues"]))
    def test_probe_generation_is_deterministic_and_self_describing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = root / "candidates.json"
            candidates.write_text(json.dumps({"build": "test-build", "candidates": [
                {"target_resource": "keen::ItemInfo", "target_field": "name"},
            ]}), encoding="utf-8")
            first = root / "first"
            second = root / "second"
            a = ResearchProbeService.generate(candidates, first)
            b = ResearchProbeService.generate(candidates, second)
            self.assertEqual(a["probe_hash"], b["probe_hash"])
            self.assertEqual(json.loads((first / "probe_manifest.json").read_text())["schema"], "control_center.research_probe.v1")
            self.assertIn("READ-ONLY", (first / "src" / "mod.lua").read_text())

    def test_cataloging_is_idempotent_and_tracks_log_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "probe.eml.log"
            log.write_text('{"fields":{"message":"[CC-RESEARCH] BEGIN|build=test"}}\n', encoding="utf-8")
            catalog = root / "catalog.json"
            first = ResearchProbeService.catalog_result(log, catalog)
            second = ResearchProbeService.catalog_result(log, catalog)
            self.assertEqual(first["log_sha256"], second["log_sha256"])
            self.assertEqual(len(ResearchProbeService.load_catalog(catalog)["entries"]), 1)

    def test_localization_probe_is_deterministic_and_bundled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entries = {"control_center.demo": {"En_Us": "Demo", "De_De": "Demo"}}
            first = ResearchProbeService.generate_localization(root / "first", entries, "build-1")
            second = ResearchProbeService.generate_localization(root / "second", entries, "build-1")
            self.assertEqual(first["probe_hash"], second["probe_hash"])
            self.assertTrue((root / "first" / "src" / "kfc_localization_registry.lua").is_file())
            self.assertIn("[CC-LOCALIZATION]", (root / "first" / "src" / "mod.lua").read_text(encoding="utf-8"))
            self.assertIn("[CC-LOCALIZATION] TAG", (root / "first" / "src" / "mod.lua").read_text(encoding="utf-8"))
            manifest = json.loads((root / "first" / "mod.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], "control_center.localization_probe.v1")
            self.assertIn("patch", manifest["capabilities"])
            self.assertFalse(manifest["collection_probe"])
            generated = (root / "first" / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertIn("skipped=safe_default_requires_explicit_opt_in", generated)

    def test_localization_collection_probe_requires_explicit_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ResearchProbeService.generate_localization(
                root / "probe", {"control_center.demo": {"En_Us": "Demo"}}, "build-1", collection_probe=True
            )
            manifest = json.loads((root / "probe" / "mod.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["collection_probe"])
            generated = (root / "probe" / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertIn("[CC-LOCALIZATION] REGISTER", generated)
            self.assertTrue(manifest["collection_probe"])

    def test_localization_catalog_records_runtime_success_without_ui_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "probe.eml.log"
            log.write_text("\n".join([
                json.dumps({"fields": {"message": "Type registry loaded successfully", "version": "1076226|branch"}}),
                json.dumps({"fields": {"message": "[CC-LOCALIZATION] REGISTER|ok=true|result=demo-guid"}}),
            ]) + "\n", encoding="utf-8")
            entry = ResearchProbeService.catalog_localization_result(log, root / "localization.json")
            self.assertEqual(entry["status"], "runtime_registration_verified")
            self.assertEqual(entry["marker_prefix"], "[CC-LOCALIZATION] ")
            self.assertEqual(entry["build"], "1076226")
            self.assertFalse(entry["ui_consumption_verified"])
            self.assertFalse(entry["promotion_ready"])
            self.assertIn("UI consumption", entry["promotion_blocker"])

    def test_content_fixture_catalog_uses_latest_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); log = root / "fixture.eml.log"
            rows = [
                {"fields": {"message": "[CC-COMBINED-LOCALIZED-BED] LOCALIZATION_TAG|ok=true|result=old"}},
                {"fields": {"message": "[CC-COMBINED-LOCALIZED-BED] STOP|donor_recipe_not_found"}},
                {"fields": {"message": "[CC-COMBINED-LOCALIZED-BED] LOCALIZATION_TAG|ok=true|result=new"}},
                {"fields": {"message": "[CC-COMBINED-LOCALIZED-BED] LOCALIZATION_COLLECTION|ok=true|result=collection"}},
                {"fields": {"message": "[CC-COMBINED-LOCALIZED-BED] REGISTERED|itemId=3987654333|recipeId=3987654334"}},
            ]
            log.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            entry = ResearchProbeService.catalog_content_fixture_result(log, root / "fixture.json")
            self.assertEqual(entry["status"], "runtime_registration_verified")
            self.assertEqual(entry["item_id"], "3987654333")
            self.assertEqual(entry["recipe_id"], "3987654334")
            self.assertTrue(any(event["message"].startswith("LOCALIZATION_TAG|") for event in entry["events"]))
            self.assertFalse(entry["ui_visual_verified"])

    def test_content_fixture_catalog_uses_latest_bed_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); log = root / "fixture.eml.log"
            rows = [
                {"fields": {"message": "[CC-BED-CLONE] DISPLAY_FIELDS|name=old"}},
                {"fields": {"message": "[CC-BED-CLONE] STOP|donor_recipe_not_found"}},
                {"fields": {"message": "[CC-BED-CLONE] DISPLAY_FIELDS|name=new"}},
                {"fields": {"message": "[CC-BED-CLONE] REGISTERED|itemId=1|recipeId=2"}},
            ]
            log.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            entry = ResearchProbeService.catalog_content_fixture_result(log, root / "fixture.json", marker="[CC-BED-CLONE]")
            self.assertEqual(entry["status"], "runtime_registration_verified")
            self.assertEqual(entry["item_id"], "1")

    def test_content_fixture_catalog_records_scoped_visual_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); log = root / "fixture.eml.log"; image = root / "bed.png"
            log.write_text(json.dumps({"fields": {"message": "[CC-BED-CLONE] DISPLAY_FIELDS|name=bed"}}) + "\n" +
                           json.dumps({"fields": {"message": "[CC-BED-CLONE] REGISTERED|itemId=1|recipeId=2"}}) + "\n", encoding="utf-8")
            image.write_bytes(b"image")
            entry = ResearchProbeService.catalog_content_fixture_result(log, root / "fixture.json", marker="[CC-BED-CLONE]", visual_evidence=image, visual_claim="additional catalog slot visible; custom label unproven")
            self.assertTrue(entry["ui_visual_verified"])
            self.assertIn("custom label unproven", entry["visual_claim"])

    def test_content_fixture_catalog_records_generated_probe_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); log = root / "generated.eml.log"
            log.write_text("\n".join(json.dumps({"fields": {"message": message}}) for message in [
                "[CC-GENERATED:probe] DONOR_CANDIDATE|noisy-guid",
                "[CC-GENERATED:probe] DONOR_SCAN_DONE|true",
                "[CC-GENERATED:probe] CLONED_ITEM|3987654524",
                "[CC-GENERATED:probe] UI_REGISTERED|true",
                "[CC-GENERATED:probe] REGISTERED_RECIPE|3987654508",
            ]) + "\n", encoding="utf-8")
            entry = ResearchProbeService.catalog_content_fixture_result(log, root / "fixture.json", marker="[CC-GENERATED:probe]")
            self.assertEqual(entry["status"], "runtime_registration_verified")
            self.assertEqual(entry["generated_item_id"], "3987654524")
            self.assertEqual(entry["generated_recipe_id"], "3987654508")
            self.assertTrue(entry["ui_registration_reported"])
            self.assertFalse(any(event["message"].startswith("DONOR_CANDIDATE|") for event in entry["events"]))

    def test_content_fixture_requires_explicit_visual_verification_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); log = root / "fixture.eml.log"; image = root / "bed.png"
            log.write_text(json.dumps({"fields": {"message": "[CC-BED-CLONE] REGISTERED|itemId=1|recipeId=2"}}) + "\n", encoding="utf-8")
            image.write_bytes(b"image")
            entry = ResearchProbeService.catalog_content_fixture_result(log, root / "fixture.json", marker="[CC-BED-CLONE]", visual_evidence=image, visual_verified=True)
            self.assertEqual(entry["status"], "end_to_end_visual_verified")
            self.assertTrue(entry["visual_verification_claimed"])

    def test_icon_import_catalog_records_runtime_chain_without_rendering_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "icon.eml.log"
            prefix = "[CC-COMBINED-LOCALIZED-BED] "
            log.write_text("\n".join(json.dumps({"fields": {"message": message}}) for message in [
                prefix + "IMPORTED_ICON|ok=true|result=f91877f0-7248-7a43-8d8c-6e9c89a53ba4",
                prefix + "REGISTERED|itemId=3987654333|recipeId=3987654334",
                prefix + "UI_LINKS|1|matching_sets=1",
            ]) + "\n", encoding="utf-8")
            entry = ResearchProbeService.catalog_icon_import_result(log, root / "icons.json", prefix)
            self.assertEqual(entry["status"], "runtime_icon_import_verified")
            self.assertFalse(entry["rendering_verified"])
            self.assertEqual(json.loads((root / "icons.json").read_text())["schema"], "control_center.icon_import_catalog.v1")

    def test_localized_bed_probe_uses_new_ids_and_bundles_helper(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ResearchProbeService.generate_localized_bed(Path(tmp) / "localized")
            root = Path(result["output"])
            source = (root / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertIn("3987654321", source)
            self.assertIn("LOCALIZATION_TAG", source)
            self.assertTrue((root / "src" / "kfc_localization_registry.lua").is_file())
            self.assertEqual(result["recipe_id"], 3987654322)
            manifest = json.loads((root / "mod.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["dependencies"][0]["id"], "bed_clone_injection_1076226")

    def test_combined_localized_bed_probe_registers_tag_before_clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ResearchProbeService.generate_combined_localized_bed(Path(tmp) / "combined")
            source = (Path(result["output"]) / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertLess(source.index("LOCALIZATION_TAG"), source.index("local ok_item"))
            self.assertIn("LOCALIZATION_COLLECTION", source)
            self.assertIn("Control Center Combined Localized Bed", source)
            self.assertIn("Older EML builds", (Path(result["output"]) / "src" / "kfc_localization_registry.lua").read_text(encoding="utf-8"))
            self.assertIn("DONOR_RECIPE_ID", source)
            self.assertIn("3987654333", source)

    def test_localization_item_transition_probe_is_research_only_and_stage_logged(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "transition"
            # Import the generator as a module so the test covers the shipped
            # CLI template without writing outside the temporary workspace.
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "build_localization_item_transition_probe",
                Path(__file__).parents[1] / "tools" / "build_localization_item_transition_probe.py",
            )
            generator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(generator)
            with patch("sys.argv", ["probe", str(output)]):
                self.assertEqual(generator.main(), 0)
            manifest = json.loads((output / "mod.json").read_text(encoding="utf-8"))
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertEqual(manifest["feature_state"], "research-only")
            self.assertIn("ITEM_CLONE", source)
            self.assertIn("COLLECTION", source)
            self.assertIn("OBJECT_ID_MUTATION", source)


if __name__ == "__main__":
    unittest.main()
