import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from core.layout_migration import LayoutMigrationError, ModLayoutMigrationService


class LayoutMigrationTests(unittest.TestCase):
    def test_import_filters_secrets_and_writes_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "old mod"; source.mkdir()
            (source / "mod.json").write_text(json.dumps({"id": "old.mod"}), encoding="utf-8")
            (source / "src").mkdir(); (source / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            (source / "nexus_api_key.json").write_text("secret", encoding="utf-8")
            imported = ModLayoutMigrationService().import_layout(source, root / "imports")
            self.assertTrue((imported / "control_center_import.json").is_file())
            self.assertFalse((imported / "nexus_api_key.json").exists())
            self.assertEqual(json.loads((imported / "control_center_import.json").read_text())["schema"], "control_center.layout_import.v1")

    def test_export_is_safe_and_excludes_secrets(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "mod"; source.mkdir()
            (source / "mod.json").write_text("{}", encoding="utf-8")
            (source / "nexus_api_key.json").write_text("secret", encoding="utf-8")
            archive = ModLayoutMigrationService().export_layout(source, root / "out.zip")
            with zipfile.ZipFile(archive) as zipped:
                self.assertIn("mod.json", zipped.namelist())
                self.assertNotIn("nexus_api_key.json", zipped.namelist())
            with self.assertRaises(LayoutMigrationError): ModLayoutMigrationService().export_layout(source, archive)

    def test_symlinked_layout_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "mod"; source.mkdir()
            target = root / "outside.txt"; target.write_text("outside", encoding="utf-8")
            link = source / "linked.txt"
            try:
                os.symlink(target, link)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable")
            with self.assertRaises(LayoutMigrationError):
                ModLayoutMigrationService().inspect(source)


if __name__ == "__main__":
    unittest.main()
