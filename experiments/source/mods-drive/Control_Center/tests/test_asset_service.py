import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from core.asset_service import AssetError, AssetService


class AssetServiceTests(unittest.TestCase):
    def test_import_and_verify_asset(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "icon.png"; source.write_bytes(b"fake-png")
            project = root / "project"; project.mkdir()
            destination = AssetService().import_file(source, project, "icons")
            self.assertTrue(destination.is_file())
            self.assertEqual(AssetService().verify(project), (True, []))

    def test_rejects_wrong_extension(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "model.txt"; source.write_text("x", encoding="utf-8")
            with self.assertRaises(AssetError): AssetService().import_file(source, root / "project", "models")

    def test_tampered_asset_fails_hash_check(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "sound.ogg"; source.write_bytes(b"sound")
            project = root / "project"; project.mkdir(); destination = AssetService().import_file(source, project, "audio")
            destination.write_bytes(b"changed")
            valid, errors = AssetService().verify(project)
            self.assertFalse(valid); self.assertTrue(errors)

    def test_unlisted_asset_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "icon.png"; source.write_bytes(b"icon")
            project = root / "project"; project.mkdir(); AssetService().import_file(source, project, "icons")
            (project / "assets" / "icons" / "extra.png").write_bytes(b"extra")
            valid, errors = AssetService().verify(project)
            self.assertFalse(valid)
            self.assertTrue(any("Unlisted asset" in error for error in errors))

    def test_manifest_size_and_kind_are_checked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "icon.png"; source.write_bytes(b"icon")
            project = root / "project"; project.mkdir(); AssetService().import_file(source, project, "icons")
            manifest = project / "assets.json"
            data = __import__("json").loads(manifest.read_text(encoding="utf-8"))
            data["assets"][0]["size"] = 999
            data["assets"][0]["kind"] = "models"
            manifest.write_text(__import__("json").dumps(data), encoding="utf-8")
            valid, errors = AssetService().verify(project)
            self.assertFalse(valid)
            self.assertTrue(any("extension" in error for error in errors))
            self.assertTrue(any("size" in error for error in errors))

    def test_model_asset_records_engine_import_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "chair.gltf"; source.write_text('{"asset":{"version":"2.0"}}', encoding="utf-8")
            project = root / "project"; project.mkdir(); AssetService().import_file(source, project, "models")
            data = __import__("json").loads((project / "assets.json").read_text(encoding="utf-8"))
            self.assertEqual(data["assets"][0]["runtime_status"], "packaged-unverified-engine-import")
            self.assertEqual(AssetService().verify(project), (True, []))

    def test_asset_provenance_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "chair.gltf"
            source.write_text('{"asset":{"version":"2.0"}}', encoding="utf-8")
            project = root / "project"; project.mkdir()
            AssetService().import_file(source, project, "models", provenance={
                "source": "original-authoring", "license": "CC-BY-4.0", "author": "Tester",
            })
            data = __import__("json").loads((project / "assets.json").read_text(encoding="utf-8"))
            self.assertEqual(data["assets"][0]["provenance"]["license"], "CC-BY-4.0")
            self.assertEqual(AssetService().verify(project), (True, []))

    def test_invalid_asset_provenance_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "chair.gltf"
            source.write_text('{"asset":{"version":"2.0"}}', encoding="utf-8")
            project = root / "project"; project.mkdir()
            with self.assertRaisesRegex(AssetError, "provenance"):
                AssetService().import_file(source, project, "models", provenance={"license": ""})

    def test_asset_reference_records_intended_resource_field(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "chair.gltf"; source.write_text('{"asset":{"version":"2.0"}}', encoding="utf-8")
            project = root / "project"; project.mkdir(); destination = AssetService().import_file(source, project, "models")
            reference = AssetService().register_reference(project, destination, "keen::ItemInfo", "iconModel", "demo:item")
            self.assertEqual(reference["status"], "reference-only")
            self.assertEqual(reference["resource_id"], "demo:item")
            self.assertEqual(AssetService().verify(project), (True, []))

    def test_duplicate_asset_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "chair.gltf"
            source.write_text('{"asset":{"version":"2.0"}}', encoding="utf-8")
            project = root / "project"; project.mkdir()
            destination = AssetService().import_file(source, project, "models")
            service = AssetService()
            service.register_reference(project, destination, "keen::ItemInfo", "iconModel", "demo:item")
            with self.assertRaisesRegex(AssetError, "already registered"):
                service.register_reference(project, destination, "keen::ItemInfo", "iconModel", "demo:item")

    def test_blank_asset_reference_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "icon.png"; source.write_bytes(b"icon")
            project = root / "project"; project.mkdir()
            destination = AssetService().import_file(source, project, "icons")
            with self.assertRaisesRegex(AssetError, "require resource_type"):
                AssetService().register_reference(project, destination, "", "iconImage")

    def test_resource_field_cannot_be_bound_to_two_assets(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); first = root / "one.png"; second = root / "two.png"
            first.write_bytes(b"one"); second.write_bytes(b"two")
            project = root / "project"; project.mkdir()
            service = AssetService()
            one = service.import_file(first, project, "icons")
            two = service.import_file(second, project, "icons")
            service.register_reference(project, one, "keen::ItemInfo", "iconImage", "demo:item")
            with self.assertRaisesRegex(AssetError, "already bound"):
                service.register_reference(project, two, "keen::ItemInfo", "iconImage", "demo:item")

    def test_verify_detects_conflicting_manifest_bindings(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); first = root / "one.png"; second = root / "two.png"
            first.write_bytes(b"one"); second.write_bytes(b"two")
            project = root / "project"; project.mkdir()
            service = AssetService()
            one = service.import_file(first, project, "icons")
            two = service.import_file(second, project, "icons")
            data = __import__("json").loads((project / "assets.json").read_text())
            data["references"] = [
                {"asset": one.relative_to(project).as_posix(), "resource_type": "keen::ItemInfo", "field": "iconImage", "resource_id": "demo:item"},
                {"asset": two.relative_to(project).as_posix(), "resource_type": "keen::ItemInfo", "field": "iconImage", "resource_id": "demo:item"},
            ]
            (project / "assets.json").write_text(__import__("json").dumps(data), encoding="utf-8")
            valid, errors = service.verify(project)
            self.assertFalse(valid)
            self.assertTrue(any("multiple assets" in error for error in errors))

    def test_malformed_gltf_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "bad.gltf"; source.write_text("not json", encoding="utf-8")
            with self.assertRaises(AssetError): AssetService().import_file(source, root / "project", "models")

    def test_import_rolls_back_asset_when_manifest_save_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "icon.png"; source.write_bytes(b"icon")
            project = root / "project"; project.mkdir()
            service = AssetService()
            with patch.object(service, "_save", side_effect=OSError("disk full")):
                with self.assertRaisesRegex(AssetError, "could not be committed"):
                    service.import_file(source, project, "icons")
            self.assertFalse((project / "assets" / "icons" / "icon.png").exists())
            self.assertFalse((project / "assets.json").exists())


if __name__ == "__main__":
    unittest.main()
