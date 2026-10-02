import json
import tempfile
import unittest
from pathlib import Path

from bridge_server import CAPABILITIES, health, modules, profile_state


class BridgeContractTests(unittest.TestCase):
    def test_health_is_read_only_and_detects_game_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            result = health(folder)
        self.assertEqual(result["schema"], "control_center.bridge_health.v1")
        self.assertTrue(result["game_folder_detected"])
        self.assertFalse(result["writes_enabled"])

    def test_module_inventory_is_structured_and_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            module_dir = Path(folder) / "modules" / "demo"
            module_dir.mkdir(parents=True)
            (module_dir / "module.json").write_text(json.dumps({
                "id": "demo",
                "name": "Demo Module",
                "version": "1.2.3",
                "feature_state": "experimental",
            }), encoding="utf-8")
            result = modules(folder)
        self.assertEqual(result[0]["id"], "demo")
        self.assertEqual(result[0]["feature_state"], "experimental")
        self.assertEqual(CAPABILITIES["operations"]["mod_install"], "disabled")

    def test_invalid_manifest_is_reported_without_failing_inventory(self):
        with tempfile.TemporaryDirectory() as folder:
            module_dir = Path(folder) / "modules" / "broken"
            module_dir.mkdir(parents=True)
            (module_dir / "module.json").write_text("not json", encoding="utf-8")
            result = modules(folder)
        self.assertEqual(result[0]["feature_state"], "invalid")
        self.assertFalse(result[0]["enabled"])

    def test_profile_state_reads_configuration_without_enabling_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "profiles").mkdir()
            (root / "runtime").mkdir()
            (root / "profiles" / "active_profile.json").write_text(json.dumps({"name": "Research", "enabled_modules": {"demo": True}, "module_settings": {"demo": {"amount": 2}}}), encoding="utf-8")
            (root / "runtime" / "live_config.json").write_text(json.dumps({"modules": {"demo": {"amount": 2}}}), encoding="utf-8")
            result = profile_state(folder)
        self.assertEqual(result["active_profile"], "Research")
        self.assertTrue(result["enabled_modules"]["demo"])
        self.assertEqual(result["module_settings"]["demo"]["amount"], 2)
        self.assertIn("demo", result["live_config_modules"])
        self.assertEqual(result["mode"], "read-only")


if __name__ == "__main__":
    unittest.main()
