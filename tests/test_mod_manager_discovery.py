import unittest

from src.mod_manager_contract import discover_package_metadata


class ModManagerDiscoveryTests(unittest.TestCase):
    def test_update_plan_is_read_only_and_backup_gated(self):
        result = discover_package_metadata(
            {"id": "sf.example", "version": "1.1.0", "build": "1076226", "files": ["mod.json", "src/mod.lua"]},
            {"id": "sf.example", "version": "1.0.0"},
        )
        self.assertEqual(result["state"], "update-available")
        self.assertEqual(result["update_plan"], {"from": "1.0.0", "to": "1.1.0"})
        self.assertTrue(result["requires_backup"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["executes_installation"])
        self.assertEqual(len(result["metadata_sha256"]), 64)

    def test_incomplete_package_is_blocked(self):
        result = discover_package_metadata({"id": "sf.example"})
        self.assertEqual(result["state"], "blocked")
        self.assertIn("version", result["missing"])
        self.assertIsNone(result["update_plan"])


if __name__ == "__main__":
    unittest.main()
