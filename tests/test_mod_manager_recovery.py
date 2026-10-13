import unittest

from src.mod_manager_contract import discover_package_metadata, simulate_update_recovery


class ModManagerRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.discovery = discover_package_metadata(
            {"id": "sf.example", "version": "1.1.0", "build": "1076226", "files": ["mod.json"]},
            {"id": "sf.example", "version": "1.0.0"},
        )

    def test_interruption_creates_plan_only_recovery_evidence(self):
        result = simulate_update_recovery(self.discovery, "interrupted")
        self.assertEqual(result["state"], "review-required")
        self.assertEqual(result["rollback"], "planned")
        self.assertFalse(result["recovery_evidence"]["mutation_performed"])
        self.assertTrue(result["requires_control_center_approval"])

    def test_missing_file_is_blocked(self):
        result = simulate_update_recovery(self.discovery, "missing-file")
        self.assertEqual(result["state"], "blocked")
        self.assertIn("required-file", result["issues"])

    def test_rollback_failure_is_visible(self):
        result = simulate_update_recovery(self.discovery, "rollback-failed")
        self.assertEqual(result["rollback"], "blocked")
        self.assertTrue(result["read_only"])


if __name__ == "__main__":
    unittest.main()
