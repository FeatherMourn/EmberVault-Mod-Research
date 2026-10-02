import json
import unittest
from pathlib import Path


class RegistryTests(unittest.TestCase):
    def test_registry_matches_manifests(self):
        root = Path(__file__).parents[1]
        registry = json.loads((root / "registry/emberworks_registry.json").read_text(encoding="utf-8"))
        manifest_ids = {json.loads(path.read_text(encoding="utf-8"))["id"] for path in root.glob("*/manifest.json")}
        registered_ids = {item["id"] for item in registry["packages"]}
        self.assertEqual(registered_ids | {registry["sdk"]}, manifest_ids)

    def test_dependencies_are_registered(self):
        root = Path(__file__).parents[1]
        registry = json.loads((root / "registry/emberworks_registry.json").read_text(encoding="utf-8"))
        ids = {item["id"] for item in registry["packages"]} | {registry["sdk"]}
        for package in registry["packages"]:
            self.assertTrue(set(package["requires"]).issubset(ids))


if __name__ == "__main__":
    unittest.main()
