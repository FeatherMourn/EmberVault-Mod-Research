import tempfile
import unittest
from pathlib import Path

from core.control_context import build_control_context


class ControlContextTests(unittest.TestCase):
    def test_context_combines_profile_mod_project_and_backup_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"; project.mkdir()
            target = root / "mods" / "demo"; target.mkdir(parents=True)
            context = build_control_context(root, {"enabled_modules": {"one": True, "two": False}}, {"demo": {"target": str(target)}}, project)
            self.assertEqual(context["profile"]["enabled_module_count"], 1)
            self.assertEqual(context["mods"]["installed_count"], 1)
            self.assertEqual(context["project"]["name"], "project")
            self.assertEqual(context["backups"]["count"], 0)

    def test_context_propagates_runtime_diagnostic_status(self):
        with tempfile.TemporaryDirectory() as td:
            context = build_control_context(Path(td), {"enabled_modules": {}}, {}, diagnostics={"diagnostics": {"status": "failed"}})
            self.assertEqual(context["runtime"]["status"], "failed")

    def test_context_carries_profile_name(self):
        with tempfile.TemporaryDirectory() as td:
            context = build_control_context(Path(td), {"enabled_modules": {}}, {}, profile_name="Safe Test")
            self.assertEqual(context["profile"]["name"], "Safe Test")

    def test_context_reports_backup_age(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); snapshot = root / "profiles" / "save-backups" / "sample"; snapshot.mkdir(parents=True)
            (snapshot / "control-center-backup.json").write_text('{"files": []}', encoding="utf-8")
            context = build_control_context(root, {"enabled_modules": {}}, {})
            self.assertIsNotNone(context["backups"]["latest_age_hours"])


if __name__ == "__main__":
    unittest.main()
