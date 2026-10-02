import json
import tempfile
import unittest
from pathlib import Path

from core.package_service import PackageError, PackageService


class PackageServiceTests(unittest.TestCase):
    def test_manifest_verify_and_export(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"; root.mkdir(); (root / "mod.lua").write_text("return {}", encoding="utf-8")
            service = PackageService(); manifest = service.create_manifest(root, "sample", "1.0.0")
            self.assertIn("mod.lua", manifest["files"])
            self.assertEqual(service.verify(root), (True, []))
            archive = service.export_zip(root, Path(td) / "sample.zip")
            self.assertTrue(archive.is_file())

    def test_hash_mismatch_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"; root.mkdir(); file = root / "mod.lua"; file.write_text("return {}", encoding="utf-8")
            service = PackageService(); service.create_manifest(root)
            file.write_text("return {changed=true}", encoding="utf-8")
            valid, errors = service.verify(root)
            self.assertFalse(valid)
            self.assertTrue(any("Hash mismatch" in error for error in errors))

    def test_export_refuses_invalid_package(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"; root.mkdir(); (root / "package.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(PackageError):
                PackageService().export_zip(root, Path(td) / "sample.zip")

    def test_unlisted_file_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"; root.mkdir(); (root / "mod.lua").write_text("return {}", encoding="utf-8")
            service = PackageService(); service.create_manifest(root)
            (root / "unexpected.lua").write_text("return {}", encoding="utf-8")
            valid, errors = service.verify(root)
            self.assertFalse(valid)
            self.assertTrue(any("Unlisted packaged file" in error for error in errors))

    def test_manifest_requires_semantic_version_and_sha256(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"; root.mkdir(); (root / "mod.lua").write_text("return {}", encoding="utf-8")
            service = PackageService(); service.create_manifest(root)
            manifest = json.loads((root / "package.json").read_text(encoding="utf-8"))
            manifest["version"] = "dev"
            manifest["files"]["mod.lua"] = "not-a-hash"
            (root / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
            valid, errors = service.verify(root)
            self.assertFalse(valid)
            self.assertTrue(any("semantic version" in error for error in errors))
            self.assertTrue(any("SHA-256" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
