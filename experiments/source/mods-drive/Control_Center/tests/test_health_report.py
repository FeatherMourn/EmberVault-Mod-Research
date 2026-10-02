import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from core.health_report import HealthReportService


class HealthReportTests(unittest.TestCase):
    def test_report_combines_runtime_modules_and_diagnostics(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "modules" / "sample").mkdir(parents=True); (base / "profiles").mkdir(parents=True)
            (base / "modules" / "sample" / "module.json").write_text(json.dumps({"id": "sample", "compatible_game_builds": [">=1070000"], "required_loader_api_version": ">=1.1"}), encoding="utf-8")
            game = Path(td) / "game"; (game / "logs").mkdir(parents=True); (game / "build.txt").write_text("1076226", encoding="utf-8")
            (game / "logs" / "latest.eml.log").write_text("REGISTERED|itemId=1\n" + json.dumps({"fields": {"message": "Lua API initialized", "api_version": "1.1"}}), encoding="utf-8")
            report = HealthReportService(base).generate(game)
            self.assertEqual(report["schema"], "control_center.health.v1")
            self.assertEqual(report["game"]["build_id"], "1076226")
            self.assertEqual(report["runtime"]["status"], "healthy")
            self.assertEqual(report["runtime"]["loader_api_version"], "1.1")
            self.assertIn("sample", report["compatibility"])
            self.assertTrue(report["compatibility"]["sample"]["compatible"])
            self.assertFalse(any("API version is unknown" in issue for issue in report["compatibility"]["sample"]["issues"]))

    def test_report_writes_atomically(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "modules").mkdir(parents=True); (base / "profiles").mkdir()
            path = Path(td) / "health.json"; HealthReportService(base).write(path)
            self.assertEqual(json.loads(path.read_text())["schema"], "control_center.health.v1")

    def test_report_includes_imported_layouts(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; imports = base / "custom_content" / "imports" / "legacy"; imports.mkdir(parents=True); (base / "modules").mkdir(parents=True); (base / "profiles").mkdir()
            (imports / "mod.json").write_text(json.dumps({"id": "legacy", "name": "Legacy", "version": "1.0.0"}), encoding="utf-8")
            report = HealthReportService(base).generate()
            self.assertEqual(len(report["content"]), 1)
            self.assertIn("legacy", report["content"][0]["project"])

    def test_report_includes_mod_inventory_and_integrity(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "modules").mkdir(parents=True); (base / "profiles").mkdir()
            game = Path(td) / "game"; mod = game / "mods" / "sample"; mod.mkdir(parents=True)
            (mod / "mod.json").write_text(json.dumps({"id": "sample", "name": "Sample", "version": "1.0.0"}), encoding="utf-8")
            (mod / "mod.lua").write_text("return {}", encoding="utf-8")
            from core.package_service import PackageService
            PackageService().create_manifest(mod, "sample", "1.0.0")
            report = HealthReportService(base).generate(game)
            self.assertEqual(report["mods"][0]["id"], "sample")
            self.assertEqual(report["mods"][0]["integrity"], "verified")

    def test_report_verifies_owned_third_party_mod_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "modules").mkdir(parents=True); (base / "profiles").mkdir(parents=True)
            game = Path(td) / "game"; mod = game / "mods" / "owned"; mod.mkdir(parents=True)
            payload = mod / "mod.json"; payload.write_text(json.dumps({"id": "owned", "version": "1.0.0"}), encoding="utf-8")
            data = mod / "mod.lua"; data.write_text("return {}", encoding="utf-8")
            digest = hashlib.sha256(data.read_bytes()).hexdigest()
            (mod / ".emh-third-party-owner.json").write_text(json.dumps({"files": {"mod.lua": digest}}), encoding="utf-8")
            report = HealthReportService(base).generate(game)
            self.assertEqual(report["mods"][0]["integrity"], "verified")
            self.assertEqual(report["mods"][0]["restore_points"], 0)
            data.write_text("tampered", encoding="utf-8")
            report = HealthReportService(base).generate(game)
            self.assertEqual(report["mods"][0]["integrity"], "failed")
            self.assertEqual(report["mods"][0]["integrity_state"], "user_modified")

    def test_report_classifies_missing_owned_files(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "modules").mkdir(parents=True); (base / "profiles").mkdir(parents=True)
            game = Path(td) / "game"; mod = game / "mods" / "owned"; mod.mkdir(parents=True)
            (mod / "mod.json").write_text(json.dumps({"id": "owned", "version": "1.0.0"}), encoding="utf-8")
            (mod / ".emh-owner.json").write_text(json.dumps({"owner": "enshrouded_mod_hub", "updated_by": "control_center", "files": {"helper.dll": "0"}}), encoding="utf-8")
            report = HealthReportService(base).generate(game)
            self.assertEqual(report["mods"][0]["integrity_state"], "missing")
            self.assertEqual(report["mods"][0]["ownership"], "control_center")

    def test_report_rejects_unsafe_owned_paths(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "modules").mkdir(parents=True); (base / "profiles").mkdir(parents=True)
            game = Path(td) / "game"; mod = game / "mods" / "owned"; mod.mkdir(parents=True)
            (mod / "mod.json").write_text(json.dumps({"id": "owned", "version": "1.0.0"}), encoding="utf-8")
            (mod / ".emh-third-party-owner.json").write_text(json.dumps({"files": {"../outside": "0"}}), encoding="utf-8")
            report = HealthReportService(base).generate(game)
            self.assertEqual(report["mods"][0]["integrity"], "failed")
            self.assertTrue(any("Unsafe owned path" in issue for issue in report["mods"][0]["integrity_errors"]))


if __name__ == "__main__":
    unittest.main()
