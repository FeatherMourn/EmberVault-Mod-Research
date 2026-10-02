import json
import unittest
from pathlib import Path

from package_mods import package_all


class PackagerTests(unittest.TestCase):
    def test_every_manifest_packages_independently(self):
        root = Path(__file__).parents[1]
        artifacts = package_all()
        manifest_ids = {json.loads(path.read_text(encoding="utf-8"))["id"] for path in root.glob("*/manifest.json")}
        self.assertEqual({path.stem.rsplit("-", 1)[0] for path in artifacts}, manifest_ids)
        self.assertTrue(all(path.stat().st_size > 0 for path in artifacts))


if __name__ == "__main__":
    unittest.main()
