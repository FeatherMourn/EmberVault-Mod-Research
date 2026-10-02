import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.installer import InstallerError, InstallerService
from core.manager import ModuleManager


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "modules" / "one").mkdir(parents=True)
        (self.root / "modules" / "one" / "module.json").write_text(json.dumps({
            "id": "one", "name": "One", "version": "1.0.0", "author": "test",
            "type": "lua_table_patch", "settings": [], "entrypoint": "patch.lua",
        }))
        (self.root / "modules" / "one" / "patch.lua").write_text("return { OnInit = function() end }\n")
        self.game = self.root / "game"
        self.game.mkdir()
        (self.game / "Enshrouded.exe").write_bytes(b"fake")
        (self.game / "mods").mkdir()
        self.manager = ModuleManager(self.root)
        self.service = InstallerService(self.root, self.manager, self.root / "staging")

    def test_install_repeat_verify_and_uninstall(self):
        manifest = json.loads(self.service.preview(self.game).files["mod.json"])
        self.assertIn("patch", manifest["capabilities"])
        plan = self.service.install(self.game)
        self.assertTrue((plan.mod_dir / "mod.json").is_file())
        owner = json.loads((plan.mod_dir / self.service.OWNER_FILE).read_text())
        self.assertEqual(owner["updated_by"], "control_center")
        self.assertIn("files", owner)
        first = (plan.mod_dir / "src" / "mod.lua").read_bytes()
        self.service.install(self.game)
        owner = json.loads((plan.mod_dir / self.service.OWNER_FILE).read_text())
        self.assertTrue(owner["previous_files"])
        self.assertEqual(first, (plan.mod_dir / "src" / "mod.lua").read_bytes())
        self.service.verify(self.game)
        self.service.uninstall(self.game)
        self.assertFalse(plan.mod_dir.exists())

    def test_proxy_is_not_overwritten(self):
        proxy = self.game / "dinput8.dll"
        proxy.write_bytes(b"third party")
        self.service.install(self.game)
        self.assertEqual(proxy.read_bytes(), b"third party")

    def test_conflict_is_actionable(self):
        second = self.root / "modules" / "two"
        second.mkdir()
        (second / "module.json").write_text(json.dumps({
            "id": "two", "name": "Two", "version": "1.0.0", "author": "test",
            "type": "lua_table_patch", "settings": [], "entrypoint": "patch.lua",
            "resource_edits": ["same"],
        }))
        (second / "patch.lua").write_text("return {}\n")
        one_manifest = json.loads((self.root / "modules" / "one" / "module.json").read_text())
        one_manifest["resource_edits"] = ["same"]
        (self.root / "modules" / "one" / "module.json").write_text(json.dumps(one_manifest))
        self.manager.active_config["enabled_modules"]["two"] = True
        with self.assertRaisesRegex(InstallerError, "Conflicting resource edit"):
            self.service.preview(self.game)

    def test_running_game_blocks_install(self):
        with patch.object(self.service, "_running", return_value=True):
            with self.assertRaisesRegex(InstallerError, "running"):
                self.service.install(self.game)

    def _require_api(self, requirement, observed=None):
        manifest_path = self.root / "modules" / "one" / "module.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["required_loader_api_version"] = requirement
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        if observed is not None:
            logs = self.game / "logs"
            logs.mkdir()
            records = [
                {"fields": {"message": "Type registry loaded successfully", "version": "1076226"}},
                {"fields": {"message": "Lua API initialized", "api_version": observed}},
            ]
            (logs / "session.eml.log").write_text("\n".join(json.dumps(row) for row in records), encoding="utf-8")

    def test_incompatible_api_blocks_install_before_game_files_change(self):
        self._require_api(">=1.2", "1.1")
        before = {p.relative_to(self.game): p.read_bytes() for p in self.game.rglob("*") if p.is_file()}
        with patch.object(self.service, "_running", return_value=False):
            with self.assertRaisesRegex(InstallerError, "requires loader API"):
                self.service.install(self.game)
        after = {p.relative_to(self.game): p.read_bytes() for p in self.game.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_required_api_without_runtime_evidence_blocks_preview(self):
        self._require_api(">=1.1")
        with self.assertRaisesRegex(InstallerError, "cannot confirm"):
            self.service.preview(self.game)

    def test_invalid_api_requirement_blocks_preview(self):
        self._require_api("latest", "1.1")
        with self.assertRaisesRegex(InstallerError, "Unsupported required_loader_api_version"):
            self.service.preview(self.game)

    def test_matching_api_allows_deployment_plan(self):
        self._require_api(">=1.1", "1.1")
        self.assertIn("src/mod.lua", self.service.preview(self.game).files)

    def test_disabled_module_api_requirement_does_not_block_other_modules(self):
        self._require_api(">=2.0", "1.1")
        self.manager.active_config["enabled_modules"]["one"] = False
        self.manager.save_profile()
        plan = self.service.preview(self.game)
        self.assertNotIn("-- Module: one", plan.files["src/mod.lua"])

    def test_failed_redeployment_restores_complete_owned_snapshot(self):
        plan = self.service.install(self.game)
        stale = plan.mod_dir / "src" / "Config" / "stale.lua"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("old config", encoding="utf-8")
        before = {p.relative_to(plan.mod_dir).as_posix(): p.read_bytes() for p in plan.mod_dir.rglob("*") if p.is_file()}
        with patch.object(self.service, "verify", side_effect=InstallerError("forced verification failure")):
            with self.assertRaisesRegex(InstallerError, "forced verification failure"):
                self.service.install(self.game)
        after = {p.relative_to(plan.mod_dir).as_posix(): p.read_bytes() for p in plan.mod_dir.rglob("*") if p.is_file()}
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
