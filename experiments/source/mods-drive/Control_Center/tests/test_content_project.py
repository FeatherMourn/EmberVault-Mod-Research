import json
import struct
import tempfile
import unittest
from pathlib import Path

from core.content_project import ContentProjectError, ContentProjectGenerator
from core.content_validation import ContentProjectValidator


class ContentProjectTests(unittest.TestCase):
    def test_generator_creates_valid_self_contained_project(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            project = ContentProjectGenerator(base, Path(td) / "identities.json").create(Path(td) / "sample", "sample_mod", "Sample Bed", "Tester")
            report = ContentProjectValidator().validate(project)
            self.assertTrue(report.valid, [issue.message for issue in report.issues])
            self.assertTrue((project / "src" / "kfc_content_registry.lua").is_file())
            self.assertTrue((project / "src" / "kfc_localization_registry.lua").is_file())
            self.assertTrue((project / "src" / "localization_payload.lua").is_file())
            self.assertTrue((project / "src" / "mod.lua").is_file())
            self.assertEqual(report.manifest["feature_state"], "research-only")
            self.assertIn("asset_dependency_tracking", report.manifest["control_center_capabilities"])
            self.assertIn("template_graph_planning", report.manifest["control_center_capabilities"])

    def test_generator_refuses_accidental_overwrite(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td) / "sample"
            destination.mkdir()
            (destination / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(ContentProjectError):
                ContentProjectGenerator(base, Path(td) / "identities.json").create(destination, "sample_mod", "Sample", "Tester")

    def test_generator_rolls_back_partial_project_and_identity_on_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); destination = root / "project"; identity_path = root / "identities.json"
            with self.assertRaises(ContentProjectError):
                ContentProjectGenerator(root, identity_path).create(destination, "sample_mod", "Sample", "Tester")
            self.assertFalse(destination.exists())
            self.assertFalse(identity_path.exists())

    def test_donor_validation_blocks_schema_type_changes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); donor_dir = root / "ItemInfo"; donor_dir.mkdir()
            (donor_dir / "donor.json").write_text('{"itemId": {"value": 1}}', encoding="utf-8")
            (donor_dir / "candidate.json").write_text('{"itemId": {"value": "wrong"}}', encoding="utf-8")
            (root / "content.json").write_text(json.dumps({
                "id": "demo", "name": "Demo", "version": "1.0.0",
                "donor_validation": [{"donor": "ItemInfo/donor.json", "candidate": "ItemInfo/candidate.json", "resource_type": "keen::ItemInfo"}],
            }), encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any(issue.code == "donor_schema.difference" for issue in report.issues))

    def test_manifest_capability_shape_is_validated(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "content.json").write_text(json.dumps({
                "id": "demo", "name": "Demo", "version": "1.0.0",
                "capabilities": ["", 7], "required_loader_api": {"bad": True},
            }), encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any(issue.code == "manifest.capabilities_invalid" for issue in report.issues))
            self.assertTrue(any(issue.code == "manifest.required_api_invalid" for issue in report.issues))

    def test_import_resource_assigns_identity_and_updates_package(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = ContentProjectGenerator(base, root / "identities.json").create(root / "project", "sample_mod", "Sample", "Tester")
            source = root / "donor.json"; source.write_text('{"itemId": {"value": 2940001508}}', encoding="utf-8")
            entry = ContentProjectGenerator(base, root / "identities.json").import_resource(project, source, "keen::ItemInfo", "palm-bed")
            imported = project / entry["path"]
            self.assertTrue(imported.is_file())
            manifest = json.loads((project / "mod.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["content"][0]["id"], "sample_mod:palm-bed")
            self.assertEqual(ContentProjectValidator().validate(project).valid, True)

    def test_import_resource_rejects_invalid_json_without_changing_project(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = ContentProjectGenerator(base, root / "identities.json").create(root / "project", "sample_mod", "Sample", "Tester")
            before = (project / "mod.json").read_bytes()
            source = root / "bad.json"; source.write_text("not json", encoding="utf-8")
            with self.assertRaises(ContentProjectError):
                ContentProjectGenerator(base, root / "identities.json").import_resource(project, source, "keen::ItemInfo")
            self.assertEqual((project / "mod.json").read_bytes(), before)

    def test_import_icon_validates_png_and_updates_asset_registry(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); generator = ContentProjectGenerator(base, root / "identities.json")
            project = generator.create(root / "project", "sample_mod", "Sample", "Tester")
            png = root / "bed.png"
            png.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 64, 32) + b"\x08\x06\x00\x00\x00")
            entry = generator.import_icon(project, png, "bed-icon")
            self.assertEqual(entry["kind"], "icons")
            self.assertEqual(entry["size"], png.stat().st_size)
            self.assertTrue((project / "assets" / "icons" / "bed.png").is_file())
            assets = json.loads((project / "assets.json").read_text())
            self.assertEqual(assets["assets"][0]["id"], "sample_mod:bed-icon")

    def test_import_icon_rejects_non_png_without_changing_project(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); generator = ContentProjectGenerator(base, root / "identities.json")
            project = generator.create(root / "project", "sample_mod", "Sample", "Tester")
            before = (project / "assets.json").read_bytes()
            source = root / "bad.png"; source.write_bytes(b"not png")
            with self.assertRaises(ContentProjectError):
                generator.import_icon(project, source)
            self.assertEqual((project / "assets.json").read_bytes(), before)

    def test_import_icon_rolls_back_when_project_validation_fails(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); generator = ContentProjectGenerator(base, root / "identities.json")
            project = generator.create(root / "project", "sample_mod", "Sample", "Tester")
            manifest_path = project / "mod.json"
            manifest = json.loads(manifest_path.read_text()); manifest["content"] = [7]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            before = (project / "assets.json").read_bytes()
            png = root / "bed.png"; png.write_bytes(b"\x89PNG\r\n\x1a\nvalid")
            with self.assertRaises(ContentProjectError):
                generator.import_icon(project, png, "rollback-icon")
            self.assertEqual((project / "assets.json").read_bytes(), before)
            self.assertFalse((project / "assets" / "icons" / "bed.png").exists())

    def test_import_resource_rolls_back_identity_on_late_validation_failure(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); identity_path = root / "identities.json"
            project = ContentProjectGenerator(base, identity_path).create(root / "project", "sample_mod", "Sample", "Tester")
            manifest_path = project / "mod.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")); manifest["content"] = [7]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            before = identity_path.read_bytes()
            source = root / "resource.json"; source.write_text('{"itemId": 1}', encoding="utf-8")
            with self.assertRaises(ContentProjectError):
                ContentProjectGenerator(base, identity_path).import_resource(project, source, "keen::ItemInfo", "late-failure")
            self.assertEqual(identity_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
