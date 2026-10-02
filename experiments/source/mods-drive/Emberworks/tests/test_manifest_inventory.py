import json
import unittest
from pathlib import Path


class ManifestInventoryTests(unittest.TestCase):
    def test_all_required_packages_have_manifests(self):
        root = Path(__file__).parents[1]
        expected = {
            "emberworks.construction_sdk",
            "emberworks.blueprint_library",
            "emberworks.worldwright",
            "emberworks.zooping",
            "emberworks.builders_wand",
            "emberworks.chiselcraft",
            "emberworks.framed_architecture",
            "emberworks.restoration",
            "emberworks.kinetic_works",
        }
        actual = {json.loads(path.read_text(encoding="utf-8"))["id"] for path in root.glob("*/manifest.json")}
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
