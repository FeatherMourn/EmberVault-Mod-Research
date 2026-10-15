import tempfile
import unittest
from pathlib import Path

from src.probe_import import import_platform_inventory


class ProbeImportTests(unittest.TestCase):
    def test_imports_checked_in_synthetic_fixture(self):
        fixture = Path(__file__).parent / "fixtures/platform_inventory_v1.tsv"
        result = import_platform_inventory(fixture, approved_root=fixture.parent, game_build="synthetic")
        self.assertEqual(len(result["records"]), 4)
        self.assertEqual(len(result["errors"]), 1)

    def test_imports_types_and_resources_with_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            export = root / "inventory.tsv"
            export.write_text("schema_version=1\ntype\tkeen::ItemInfo\nresource\tguid-1\tkeen::ItemInfo\t0\n", encoding="utf-8")
            result = import_platform_inventory(export, approved_root=root, game_build="25936191")
            self.assertEqual(len(result["records"]), 2)
            self.assertEqual(len(result["source_sha256"]), 64)
            self.assertTrue(result["read_only"])

    def test_rejects_unversioned_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            export = root / "inventory.tsv"
            export.write_text("type\tkeen::ItemInfo\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                import_platform_inventory(export, approved_root=root)


if __name__ == "__main__":
    unittest.main()
