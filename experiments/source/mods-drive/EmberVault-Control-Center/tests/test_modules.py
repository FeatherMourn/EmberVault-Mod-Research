import json
import tempfile
import unittest
from pathlib import Path

from core.modules import LaunchContext, ModuleRegistry
from core.application import EmbervaultRuntime


class ModuleRegistryTests(unittest.TestCase):
    def test_discovers_manifest_and_capability(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "demo"
            module.mkdir()
            (module / "module.json").write_text(json.dumps({
                "id": "embervault.demo", "name": "Demo", "version": "1.0.0",
                "publisher": "Test", "capabilities": ["demo.read"],
            }))
            registry = ModuleRegistry(Path(temp))
            modules = registry.discover()
            self.assertEqual(modules["embervault.demo"].name, "Demo")
            self.assertEqual([m.id for m in registry.by_capability("demo.read")], ["embervault.demo"])

    def test_discovery_ignores_malformed_manifests(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "broken"
            module.mkdir()
            (module / "module.json").write_text("not json")
            discovered = ModuleRegistry(Path(temp)).discover()
            self.assertNotIn("broken", discovered)
            self.assertIn("embervault.example", discovered)

    def test_high_risk_launch_is_denied_before_process_start(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "default")
            decision = runtime.launcher.check("trainer", "trainer", profile)
            self.assertFalse(decision.allowed)
            self.assertIn("Research profile", decision.reasons[0])

    def test_clean_registry_discovers_seed_example_module(self):
        with tempfile.TemporaryDirectory() as temp:
            registry = ModuleRegistry(Path(temp))
            self.assertEqual(list(registry.discover()), ["embervault.content-creator", "embervault.example", "embervault.research", "embervault.trainer", "embervault.tuning-audit"])

    def test_embedded_module_loads_inside_package_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            registry = ModuleRegistry(Path(temp))
            registry.discover()
            self.assertEqual([item.id for item in registry.embedded()], ["embervault.example"])
            module = registry.load_embedded("embervault.example")
            self.assertEqual(module.describe()["execution"], "embedded")

    def test_registry_merges_seed_and_runtime_modules(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "local").mkdir()
            (root / "local" / "module.json").write_text(json.dumps({
                "id": "local.module", "name": "Local", "version": "1.0.0", "publisher": "Test",
            }))
            discovered = ModuleRegistry(root).discover()
            self.assertIn("local.module", discovered)
            self.assertIn("embervault.example", discovered)

    def test_guarded_content_launch_requires_recovery_token(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "research")
            save_dir = Path(temp) / "save-source"
            save_dir.mkdir()
            (save_dir / "world.dat").write_text("safe", encoding="utf-8")
            backup = runtime.saves.backup(save_dir)
            with self.assertRaises(PermissionError):
                runtime.launcher.launch(
                    "embervault.content-creator", "content-creator", profile,
                    LaunchContext(profile.id, None, "EV-OP-CONTENT"),
                )
            process = runtime.launcher.launch(
                "embervault.content-creator", "content-creator", profile,
                LaunchContext(profile.id, None, "EV-OP-CONTENT"), backup.id,
            )
            process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0)

    def test_guarded_research_launch_succeeds_in_research_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "research")
            process = runtime.launcher.launch(
                "embervault.research", "research", profile,
                LaunchContext(profile.id, None, "EV-OP-RESEARCH"),
            )
            process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0)

    def test_module_launcher_rejects_executable_outside_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            module = root / "demo"
            module.mkdir()
            (module / "module.json").write_text(json.dumps({
                "id": "demo.unsafe", "name": "Unsafe", "version": "1.0.0",
                "publisher": "Test", "executable": "../outside.py",
            }))
            (root / "outside.py").write_text("print('no')")
            registry = ModuleRegistry(root)
            registry.discover()
            with self.assertRaises(ValueError):
                registry.launch("demo.unsafe", LaunchContext("default", None, None))

    def test_module_manifest_rejects_path_like_id(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "bad"
            module.mkdir()
            (module / "module.json").write_text(json.dumps({
                "id": "../escape", "name": "Bad", "version": "1.0.0", "publisher": "Test",
            }))
            discovered = ModuleRegistry(Path(temp)).discover()
            self.assertNotIn("../escape", discovered)
            self.assertIn("embervault.example", discovered)

    def test_module_manifest_rejects_unsafe_executable_declaration(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "unsafe"
            module.mkdir()
            (module / "module.json").write_text(json.dumps({
                "id": "unsafe", "name": "Unsafe", "version": "1.0.0",
                "publisher": "Test", "executable": "../outside.py",
            }))
            discovered = ModuleRegistry(Path(temp)).discover()
            self.assertNotIn("unsafe", discovered)
            self.assertIn("embervault.example", discovered)

    def test_module_manifest_requires_capability_array(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "bad"
            module.mkdir()
            (module / "module.json").write_text(json.dumps({
                "id": "bad.capabilities", "name": "Bad", "version": "1.0.0",
                "publisher": "Test", "capabilities": "trainer",
            }))
            discovered = ModuleRegistry(Path(temp)).discover()
            self.assertNotIn("bad.capabilities", discovered)

    def test_module_manifest_rejects_blank_or_duplicate_capabilities(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "bad"
            module.mkdir()
            (module / "module.json").write_text(json.dumps({
                "id": "bad.capabilities", "name": "Bad", "version": "1.0.0",
                "publisher": "Test", "capabilities": ["trainer", "trainer", ""],
            }))
            self.assertNotIn("bad.capabilities", ModuleRegistry(Path(temp)).discover())

    def test_module_manifest_rejects_non_string_capability_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "bad"
            module.mkdir()
            (module / "module.json").write_text(json.dumps({
                "id": "bad.entries", "name": "Bad", "version": "1.0.0",
                "publisher": "Test", "capabilities": ["trainer", 12],
            }))
            self.assertNotIn("bad.entries", ModuleRegistry(Path(temp)).discover())

    def test_module_manifest_rejects_windows_absolute_executable_path(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "bad"
            module.mkdir()
            (module / "module.json").write_text(json.dumps({
                "id": "bad.windows-path", "name": "Bad", "version": "1.0.0",
                "publisher": "Test", "executable": "C:\\outside.py",
            }))
            self.assertNotIn("bad.windows-path", ModuleRegistry(Path(temp)).discover())

    def test_module_manifest_rejects_unknown_feature_state(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "bad"
            module.mkdir()
            (module / "module.json").write_text(json.dumps({
                "id": "bad.state", "name": "Bad", "version": "1.0.0",
                "publisher": "Test", "feature_state": "mystery",
            }))
            self.assertNotIn("bad.state", ModuleRegistry(Path(temp)).discover())

    def test_module_manifest_exposes_explicit_process_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "embedded").mkdir()
            (root / "embedded" / "module.json").write_text(json.dumps({
                "id": "embedded.module", "name": "Embedded", "version": "1.0",
                "publisher": "Test", "capabilities": ["inspect"],
                "process_mode": "embedded", "entrypoint": "module.py",
            }))
            (root / "separate").mkdir()
            (root / "separate" / "module.json").write_text(json.dumps({
                "id": "separate.module", "name": "Separate", "version": "1.0",
                "publisher": "Test", "capabilities": ["audit"],
                "process_mode": "separate", "executable": "worker.py",
            }))
            discovered = ModuleRegistry(root).discover()
            self.assertEqual(discovered["embedded.module"].process_mode, "embedded")
            self.assertEqual(discovered["separate.module"].process_mode, "separate")

    def test_module_manifest_rejects_process_mode_launch_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "modules"
            root.mkdir()
            for name, mode, launcher in (("embedded-bad", "embedded", "executable"), ("separate-bad", "separate", "entrypoint")):
                directory = root / name
                directory.mkdir()
                payload = {
                    "id": f"embervault.{name}", "name": name, "version": "1.0",
                    "publisher": "Test", "capabilities": ["inspect"],
                    "process_mode": mode, launcher: "worker.py",
                }
                (directory / "module.json").write_text(json.dumps(payload))
            discovered = ModuleRegistry(root).discover()
            self.assertNotIn("embervault.embedded-bad", discovered)
            self.assertNotIn("embervault.separate-bad", discovered)

    def test_module_manifest_requires_string_identity_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "bad"
            module.mkdir()
            (module / "module.json").write_text(json.dumps({
                "id": "bad.identity", "name": 12, "version": "1.0.0", "publisher": "Test",
            }))
            self.assertNotIn("bad.identity", ModuleRegistry(Path(temp)).discover())

    def test_python_module_process_uses_current_interpreter(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "demo"
            module.mkdir()
            (module / "module.json").write_text(json.dumps({
                "id": "demo.process", "name": "Demo", "version": "1.0.0",
                "publisher": "Test", "executable": "process.py",
            }))
            (module / "process.py").write_text("import sys; print(sys.argv[1])")
            registry = ModuleRegistry(Path(temp))
            registry.discover()
            process = registry.launch("demo.process", __import__("core.modules", fromlist=["LaunchContext"]).LaunchContext("default", "", None))
            process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0)

    def test_guarded_trainer_launch_succeeds_with_research_and_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "research")
            save_dir = Path(temp) / "save-source"
            save_dir.mkdir()
            (save_dir / "world.dat").write_text("safe", encoding="utf-8")
            backup = runtime.saves.backup(save_dir)
            process = runtime.launcher.launch(
                "embervault.trainer", "trainer", profile,
                LaunchContext(profile.id, None, "EV-OP-TEST"), backup.id,
            )
            process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0)

    def test_guarded_worker_reports_read_only_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "research")
            process = runtime.launcher.launch(
                "embervault.research", "research", profile,
                LaunchContext(profile.id, "C:/Game", "EV-OP-CONTRACT"),
            )
            output, _ = process.communicate(timeout=5)
            result = json.loads(output)
            self.assertEqual(result["contract_version"], 1)
            self.assertTrue(result["read_only"])
            self.assertEqual(result["game_path"], "C:/Game")

    def test_trainer_worker_reports_readiness_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "research")
            save_dir = Path(temp) / "save-source"
            save_dir.mkdir()
            (save_dir / "world.dat").write_text("safe", encoding="utf-8")
            backup = runtime.saves.backup(save_dir)
            process = runtime.launcher.launch(
                "embervault.trainer", "trainer", profile,
                LaunchContext(profile.id, temp, "EV-OP-TRAINER", backup.id), backup.id,
            )
            result = json.loads(process.communicate(timeout=5)[0])
            self.assertIn("recovery_backup_supplied: True", result["checks"])
            self.assertIn("mutation_performed: False", result["checks"])

    def test_content_worker_reports_design_boundary_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "research")
            save_dir = Path(temp) / "save-source"
            save_dir.mkdir()
            (save_dir / "world.dat").write_text("safe", encoding="utf-8")
            backup = runtime.saves.backup(save_dir)
            process = runtime.launcher.launch(
                "embervault.content-creator", "content-creator", profile,
                LaunchContext(profile.id, temp, "EV-OP-CONTENT", backup.id), backup.id,
            )
            result = json.loads(process.communicate(timeout=5)[0])
            self.assertIn("design_workspace_only: True", result["checks"])
            self.assertIn("live_game_content_touched: False", result["checks"])

    def test_tuning_audit_reports_staged_only_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "research")
            process = runtime.launcher.launch(
                "embervault.tuning-audit", "tuning-audit", profile,
                LaunchContext(profile.id, temp, "EV-OP-TUNING"),
            )
            result = json.loads(process.communicate(timeout=5)[0])
            self.assertTrue(result["read_only"])
            self.assertIn("settings_source: staged-profile-values", result["checks"])
            self.assertIn("live_game_settings_changed: False", result["checks"])

    def test_tuning_audit_validates_staged_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "research")
            manifest = runtime.game_settings.export(profile)
            process = runtime.launcher.launch(
                "embervault.tuning-audit", "tuning-audit", profile,
                LaunchContext(profile.id, temp, "EV-OP-TUNING-MANIFEST", None, str(manifest)),
            )
            result = json.loads(process.communicate(timeout=5)[0])
            self.assertIn("settings_manifest_valid: True", result["checks"])

    def test_research_worker_reports_read_only_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "research")
            process = runtime.launcher.launch(
                "embervault.research", "research", profile,
                LaunchContext(profile.id, temp, "EV-OP-EVIDENCE"),
            )
            output, _ = process.communicate(timeout=5)
            result = json.loads(output)
            self.assertTrue(result["read_only"])
            self.assertGreaterEqual(len(result["evidence"]), 3)
            self.assertIn("game_path_exists: True", result["evidence"])

    def test_launch_rejects_capability_not_declared_by_module(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "research")
            save_dir = Path(temp) / "save-source"
            save_dir.mkdir()
            (save_dir / "world.dat").write_text("safe", encoding="utf-8")
            backup = runtime.saves.backup(save_dir)
            decision = runtime.launcher.check("embervault.research", "trainer", profile, backup.id)
            self.assertFalse(decision.allowed)
            self.assertIn("does not declare", decision.reasons[-1])


if __name__ == "__main__":
    unittest.main()
