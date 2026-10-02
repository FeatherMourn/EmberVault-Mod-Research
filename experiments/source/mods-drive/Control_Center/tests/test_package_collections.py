import json
import tempfile
import unittest
from pathlib import Path

from core.package_collections import PackageCollectionService
from core.package_security import PackageSecurityService


class PackageCollectionTests(unittest.TestCase):
    def test_catalogs_compatibility_and_integrity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "packages"; package = root / "demo"; package.mkdir(parents=True)
            (package / "mod.json").write_text(json.dumps({"id": "demo", "version": "1.0.0", "author": "Tester", "compatible_game_builds": ["=1076226"]}), encoding="utf-8")
            (package / "mod.lua").write_text("return {}", encoding="utf-8")
            PackageSecurityService().create_lock(package)
            entries = PackageCollectionService().scan(root, "1076226")
            self.assertEqual(entries[0].compatibility, "compatible")
            self.assertEqual(entries[0].integrity, "verified")

    def test_unknown_build_is_not_claimed_compatible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "packages"; package = root / "demo"; package.mkdir(parents=True)
            (package / "mod.json").write_text(json.dumps({"id": "demo", "version": "1.0.0", "compatible_game_builds": ["=1076226"]}), encoding="utf-8")
            self.assertEqual(PackageCollectionService().scan(root, None)[0].compatibility, "unknown")


if __name__ == "__main__":
    unittest.main()
