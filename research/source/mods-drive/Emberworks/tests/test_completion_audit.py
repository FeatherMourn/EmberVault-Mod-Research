import json
import subprocess
import sys
import unittest
from pathlib import Path


class CompletionAuditTests(unittest.TestCase):
    def test_audit_is_conservative(self):
        root = Path(__file__).parents[1]
        result = subprocess.run([sys.executable, "completion_audit.py"], cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        report = json.loads((root / "COMPLETION_AUDIT.json").read_text(encoding="utf-8"))
        self.assertEqual(report["manifest_count"], 9)
        self.assertEqual(report["missing_packages"], [])
        self.assertEqual(report["unexpected_packages"], [])
        self.assertTrue(report["distribution_wheel"]["present"])
        self.assertTrue(report["distribution_wheel"]["content_valid"])
        self.assertTrue(report["build_status_consistent"])
        self.assertTrue(report["automated_tests"]["passed"])
        self.assertFalse(report["runtime_probe"]["construction_mutation_verified"])
        self.assertTrue(report["native_bridge"]["host_load_verified"])
        self.assertFalse(report["native_bridge"]["in_game_module_loaded"])
        self.assertTrue(report["resource_creation_probe"]["create_resource_succeeded"])
        self.assertTrue(report["resource_creation_probe"]["voxel_resource_succeeded"])
        self.assertTrue(report["resource_creation_probe"]["render_resource_succeeded"])
        self.assertTrue(report["resource_creation_probe"]["item_registry_insert_succeeded"])
        self.assertTrue(report["resource_creation_probe"]["recipe_registry_insert_succeeded"])
        self.assertTrue(report["ui_probe"]["executed"])
        self.assertFalse(report["ui_probe"]["recipe_linkage_verified"])
        self.assertEqual(report["completion"]["status"], "incomplete")
        self.assertIn("native bridge", report["completion"]["reason"])


if __name__ == "__main__":
    unittest.main()
