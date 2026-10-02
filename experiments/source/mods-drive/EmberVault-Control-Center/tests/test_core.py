import json
import shutil
import tempfile
import unittest
import zipfile
from unittest import mock
from pathlib import Path

from core.compatibility import CompatibilityState, evaluate
from core.logging_service import StructuredLogService
from core.operations import OperationService, OperationStatus
from core.integration import IntegrationContext
from core.profiles import Profile, ProfileService
from core.packages import PackageManifest, PackageService
from core.game_settings import GameSettingsService
from core.risk import RiskGateService
from core.settings import Settings, SettingsService
from core.save_manager import SaveManagerService


class CoreServiceTests(unittest.TestCase):
    def test_integration_context_preserves_cross_module_safety_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            service = OperationService(Path(temp) / "operations.jsonl")
            operation = service.start(
                "research-evidence", profile_id="research", capability="research",
                capability_state="read-only", recovery_expectation="no live mutation")
            context = IntegrationContext.from_operation(
                operation, capability="research", capability_state="read-only",
                recovery_expectation="no live mutation")
            self.assertEqual(context.operation_id, operation.id)
            self.assertEqual(context.profile_id, "research")
            self.assertEqual(context.as_dict()["recovery_expectation"], "no live mutation")
            self.assertEqual(service.integration_context(operation), context)
            saved = service.list_recent()[0]
            self.assertEqual(saved.capability_state, "read-only")
            self.assertEqual(saved.recovery_expectation, "no live mutation")

    def test_integration_context_rejects_missing_identity_or_unknown_state(self):
        with self.assertRaises(ValueError):
            IntegrationContext("", "research", "research", "read-only", "safe")
        with self.assertRaises(ValueError):
            IntegrationContext("op", "research", "research", "unsafe", "safe")
    def test_settings_round_trip_is_atomic_and_typed(self):
        with tempfile.TemporaryDirectory() as temp:
            service = SettingsService(Path(temp))
            service.save(Settings(game_path="C:/Enshrouded", advanced_mode=True))
            loaded = service.load()
            self.assertEqual(loaded.game_path, "C:/Enshrouded")
            self.assertTrue(loaded.advanced_mode)

    def test_profiles_create_safe_defaults(self):
        with tempfile.TemporaryDirectory() as temp:
            profiles = ProfileService(Path(temp)).ensure_defaults()
            self.assertEqual({p.id for p in profiles}, {"default", "research"})

    def test_profile_defaults_have_distinct_safety_purposes(self):
        with tempfile.TemporaryDirectory() as temp:
            profiles = ProfileService(Path(temp)).ensure_defaults()
            by_id = {profile.id: profile for profile in profiles}
            self.assertEqual(by_id["default"].profile_type, "stable")
            self.assertEqual(by_id["research"].profile_type, "research")

    def test_profiles_restore_missing_builtin_default(self):
        with tempfile.TemporaryDirectory() as temp:
            service = ProfileService(Path(temp))
            service.save(Profile("default", "Default", "Existing", "stable"))
            restored = service.ensure_defaults()
            self.assertEqual({profile.id for profile in restored}, {"default", "research"})
            self.assertEqual(next(item for item in restored if item.id == "default").description, "Existing")

    def test_profiles_normalize_corrupt_package_and_settings_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            service = ProfileService(Path(temp))
            service.save(Profile("default", "Default", enabled_packages=["safe.mod"], settings={"speed": 1}))
            path = Path(temp) / "profiles" / "default.json"
            raw = json.loads(path.read_text())
            raw["enabled_packages"] = ["safe.mod", 12, ""]
            raw["settings"] = ["corrupt"]
            path.write_text(json.dumps(raw))
            profile = service.list()[0]
            self.assertEqual(profile.enabled_packages, ["safe.mod"])
            self.assertEqual(profile.settings, {})

    def test_profiles_ignore_duplicate_ids_deterministically(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "profiles"
            directory.mkdir()
            first = {"id": "same", "name": "First", "profile_type": "custom"}
            second = {"id": "same", "name": "Second", "profile_type": "custom"}
            (directory / "a.json").write_text(json.dumps(first))
            (directory / "b.json").write_text(json.dumps(second))
            profiles = ProfileService(Path(temp)).list()
            self.assertEqual([(item.id, item.name) for item in profiles], [("same", "First")])

    def test_profiles_skip_invalid_persisted_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "profiles"
            directory.mkdir()
            (directory / "empty.json").write_text(json.dumps({"id": "", "name": "Nope"}))
            (directory / "path.json").write_text(json.dumps({"id": "../escape", "name": "Nope"}))
            (directory / "blank-name.json").write_text(json.dumps({"id": "valid", "name": "  "}))
            self.assertEqual(ProfileService(Path(temp)).list(), [])

    def test_custom_profile_creation_generates_safe_id(self):
        with tempfile.TemporaryDirectory() as temp:
            service = ProfileService(Path(temp))
            service.ensure_defaults()
            profile = service.create_custom("My Test World")
            self.assertEqual(profile.id, "my-test-world")
            self.assertEqual(profile.profile_type, "custom")

    def test_built_in_profiles_cannot_be_deleted(self):
        with tempfile.TemporaryDirectory() as temp:
            service = ProfileService(Path(temp))
            service.ensure_defaults()
            with self.assertRaises(ValueError):
                service.delete_custom("default")

    def test_structured_log_contains_contract_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "logs" / "events.jsonl"
            StructuredLogService(path).info("Started", operation_id="EV-OP-1", profile_id="default")
            record = json.loads(path.read_text().splitlines()[0])
            self.assertEqual(record["operation_id"], "EV-OP-1")
            self.assertEqual(record["profile_id"], "default")

    def test_structured_log_tolerates_non_json_details(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "logs" / "events.jsonl"
            StructuredLogService(path).info("Diagnostic", details={"path": Path(temp)})
            record = json.loads(path.read_text().splitlines()[0])
            self.assertEqual(record["details"]["path"], str(Path(temp)))

    def test_operation_lifecycle_records_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            service = OperationService(Path(temp) / "operations.jsonl")
            operation = service.start("backup", profile_id="default")
            service.finish(operation, OperationStatus.SUCCEEDED, "Verified", "EV-BACKUP-1")
            records = [json.loads(line) for line in service.path.read_text().splitlines()]
            self.assertEqual(records[-1]["status"], "succeeded")
            self.assertEqual(records[-1]["backup_id"], "EV-BACKUP-1")

    def test_recent_operations_returns_latest_records_first(self):
        with tempfile.TemporaryDirectory() as temp:
            service = OperationService(Path(temp) / "operations.jsonl")
            first = service.start("first")
            service.finish(first, OperationStatus.SUCCEEDED, "done")
            second = service.start("second")
            service.finish(second, OperationStatus.FAILED, "broken")
            recent = service.list_recent(2)
            self.assertEqual([item.operation_type for item in recent], ["second", "first"])

    def test_recent_operations_skips_corrupt_history_lines(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "operations.jsonl"
            service = OperationService(path)
            operation = service.start("valid")
            path.write_text(path.read_text(encoding="utf-8") + "not-json\n", encoding="utf-8")
            self.assertEqual([item.operation_type for item in service.list_recent()], ["valid"])

    def test_recent_operations_skips_invalid_operation_contracts(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "operations.jsonl"
            path.write_text("\n".join([
                json.dumps({"id": "", "operation_type": "backup", "started_at": "now"}),
                json.dumps({"id": "EV-OP-BAD", "operation_type": "backup", "started_at": "now", "status": "unknown"}),
                json.dumps({"id": "EV-OP-GOOD", "operation_type": "backup", "started_at": "now", "status": "succeeded"}),
            ]))
            self.assertEqual([item.id for item in OperationService(path).list_recent()], ["EV-OP-GOOD"])

    def test_settings_preserve_game_folder_for_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            service = SettingsService(Path(temp))
            service.save(Settings(game_path="C:/Games/Enshrouded"))
            self.assertEqual(service.load().game_path, "C:/Games/Enshrouded")

    def test_settings_normalize_corrupt_value_types(self):
        with tempfile.TemporaryDirectory() as temp:
            service = SettingsService(Path(temp))
            service.path.write_text(json.dumps({
                "game_path": 12, "backup_directory": [], "update_channel": "",
                "theme": None, "advanced_mode": "yes",
            }))
            settings = service.load()
            self.assertIsNone(settings.game_path)
            self.assertIsNone(settings.backup_directory)
            self.assertEqual(settings.update_channel, "stable")
            self.assertEqual(settings.theme, "ember-dark")
            self.assertFalse(settings.advanced_mode)

    def test_unknown_compatibility_is_not_compatible(self):
        result = evaluate(required_builds=["1076226"], detected_build=None)
        self.assertEqual(result.state, CompatibilityState.UNKNOWN)

    def test_compatibility_ignores_blank_build_evidence(self):
        result = evaluate(required_builds=["", "  "], detected_build="  ")
        self.assertEqual(result.state, CompatibilityState.UNKNOWN)

    def test_compatibility_normalizes_warning_messages(self):
        result = evaluate(required_builds=["123"], detected_build="123", warnings=["  caution  ", 12, ""])
        self.assertEqual(result.reasons, ("caution",))

    def test_package_enablement_is_profile_scoped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package_dir = root / "packages" / "demo"
            package_dir.mkdir(parents=True)
            (package_dir / "package.json").write_text(json.dumps({
                "id": "demo.mod", "name": "Demo Mod", "version": "1.0.0"
            }))
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            packages = PackageService(root, profiles)
            packages.discover()
            default = profiles.list()[0]
            updated = packages.set_enabled(default, "demo.mod", True)
            self.assertEqual(updated.enabled_packages, ["demo.mod"])
            research = next(profile for profile in profiles.list() if profile.id == "research")
            self.assertFalse(packages.is_enabled(research, "demo.mod"))

    def test_game_settings_are_stored_on_selected_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            service = GameSettingsService(profiles)
            profile = profiles.list()[0]
            updated = service.stage(profile, "enemy_damage_multiplier", 1.5)
            self.assertEqual(service.values(updated)["enemy_damage_multiplier"], 1.5)

    def test_game_settings_reset_restores_documented_defaults(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            service = GameSettingsService(profiles)
            profile = profiles.list()[0]
            changed = service.stage(profile, "enemy_damage_multiplier", 2.0)
            reset = service.reset(changed)
            self.assertEqual(service.values(reset)["enemy_damage_multiplier"], 1.0)

    def test_game_settings_export_is_outside_game_and_marks_staged_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            service = GameSettingsService(profiles)
            profile = service.stage(profiles.list()[0], "resource_yield_multiplier", 2.0)
            destination = service.export(profile)
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(payload["application_state"], "staged-only")
            self.assertEqual(payload["settings"]["resource_yield_multiplier"], 2.0)
            self.assertNotIn("game", destination.parts)

    def test_game_settings_contract_declares_staged_only_boundary(self):
        schema = json.loads((Path(__file__).parents[1] / "contracts" / "game-settings.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["application_state"]["const"], "staged-only")
        self.assertIn("settings", schema["required"])

    def test_game_settings_import_requires_matching_staged_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            profiles = ProfileService(Path(temp))
            profiles.ensure_defaults()
            service = GameSettingsService(profiles)
            profile = profiles.list()[0]
            manifest = Path(temp) / "settings.json"
            manifest.write_text(json.dumps({
                "schema_version": 1,
                "profile_id": profile.id,
                "application_state": "staged-only",
                "settings": {
                    "enemy_damage_multiplier": 1.5,
                    "resource_yield_multiplier": 2.0,
                    "experimental_rules": True,
                    "base_crit_chance": 0.2,
                },
            }), encoding="utf-8")
            updated = service.import_manifest(profile, manifest)
            self.assertEqual(service.values(updated)["resource_yield_multiplier"], 2.0)
            self.assertTrue(service.values(updated)["experimental_rules"])
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["profile_id"] = "other-profile"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                service.import_manifest(updated, manifest)

    def test_project_export_contracts_declare_safe_application_states(self):
        root = Path(__file__).parents[1] / "contracts"
        character = json.loads((root / "character-plan.schema.json").read_text(encoding="utf-8"))
        content = json.loads((root / "content-project.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(character["properties"]["application_state"]["const"], "plan-only")
        self.assertEqual(content["properties"]["application_state"]["const"], "design-only")
        knowledge = json.loads((root / "knowledge-entry.schema.json").read_text(encoding="utf-8"))
        self.assertIn("published_at", knowledge["required"])

    def test_game_settings_reject_out_of_range_or_non_finite_numbers(self):
        with tempfile.TemporaryDirectory() as temp:
            profiles = ProfileService(Path(temp))
            profiles.ensure_defaults()
            service = GameSettingsService(profiles)
            profile = profiles.list()[0]
            for value in (0, 4.1, float("nan"), float("inf"), True):
                with self.assertRaises(ValueError):
                    service.stage(profile, "enemy_damage_multiplier", value)

    def test_game_settings_normalize_corrupt_profile_values(self):
        with tempfile.TemporaryDirectory() as temp:
            profiles = ProfileService(Path(temp))
            profiles.ensure_defaults()
            profile = profiles.list()[0]
            corrupt = Profile(**{**profile.__dict__, "settings": {
                "enemy_damage_multiplier": "not-a-number", "experimental_rules": "yes",
            }})
            self.assertEqual(GameSettingsService(profiles).values(corrupt), {
                "enemy_damage_multiplier": 1.0,
                "resource_yield_multiplier": 1.0,
                "experimental_rules": False,
                "base_crit_chance": 0.1,
            })

    def test_high_risk_capabilities_require_research_and_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            profiles = ProfileService(Path(temp))
            profiles.ensure_defaults()
            stable, research = profiles.list()
            saves = SaveManagerService(Path(temp))
            source = Path(temp) / "save-source"
            source.mkdir()
            (source / "world.dat").write_text("safe", encoding="utf-8")
            backup = saves.backup(source)
            gate = RiskGateService(saves)
            self.assertFalse(gate.evaluate("trainer", stable).allowed)
            self.assertFalse(gate.evaluate("trainer", research).allowed)
            self.assertFalse(gate.evaluate("trainer", research, verified_backup_id="EV-BACKUP-FAKE").allowed)
            self.assertTrue(gate.evaluate("trainer", research, verified_backup_id=backup.id).allowed)
            (Path(temp) / "backups" / backup.id / "save" / "world.dat").write_text("tampered", encoding="utf-8")
            self.assertFalse(gate.evaluate("trainer", research, verified_backup_id=backup.id).allowed)

    def test_package_import_requires_manifest_and_copies_valid_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            source = root / "incoming"
            source.mkdir()
            (source / "package.json").write_text(json.dumps({"id": "imported.mod", "name": "Imported", "version": "1.0.0"}))
            service = PackageService(root, profiles)
            package = service.install_from_directory(source)
            self.assertEqual(package.id, "imported.mod")
            self.assertTrue((root / "packages" / "imported.mod" / "package.json").exists())
            self.assertEqual(list(root.glob("embervault-package-stage-*")), [])

    def test_external_mod_json_is_adapted_without_mutating_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            source = root / "external-mod"
            source.mkdir()
            (source / "mod.json").write_text(json.dumps({
                "id": "external.flight", "name": "Flight", "version": "2.0",
                "author": "Community", "entrypoint": "src/mod.lua",
            }))
            (source / "mod.lua").write_text("return {}")
            service = PackageService(root, profiles)
            package = service.install_from_directory(source)
            self.assertEqual(package.package_type, "mod")
            self.assertTrue((root / "packages" / "external.flight" / "package.json").exists())
            self.assertTrue((source / "mod.json").exists())

    def test_external_mod_archive_is_adapted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            archive = root / "external.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("community/mod.json", json.dumps({
                    "id": "community.mod", "name": "Community", "version": "1.2",
                }))
                bundle.writestr("community/mod.lua", "return {}")
            package = PackageService(root, profiles).install_from_archive(archive)
            self.assertEqual(package.id, "community.mod")
            self.assertTrue((root / "packages" / "community.mod" / "package.json").exists())

    def test_external_mod_inspection_is_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            mods = root / "game" / "mods"
            mods.mkdir(parents=True)
            folder = mods / "existing"
            folder.mkdir()
            (folder / "mod.json").write_text(json.dumps({"id": "existing.mod", "name": "Existing", "version": "1.0"}))
            service = PackageService(root, profiles)
            found = service.inspect_external(mods)
            self.assertEqual([item.id for item in found], ["existing.mod"])
            self.assertFalse((root / "packages" / "existing.mod").exists())

    def test_deployment_plan_is_read_only_and_reports_conflicts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            source = root / "incoming"
            source.mkdir()
            (source / "package.json").write_text(json.dumps({"id": "planned.mod", "name": "Planned", "version": "1.0"}))
            service = PackageService(root, profiles)
            package = service.install_from_directory(source)
            profile = profiles.list()[0]
            profile = service.set_enabled(profile, package.id, True)
            game = root / "game"
            plan = service.deployment_plan(profile, game)
            self.assertEqual(plan[0].status, "ready")
            self.assertFalse(game.exists())
            game.joinpath("mods", package.id).mkdir(parents=True)
            self.assertEqual(service.deployment_plan(profile, game)[0].status, "conflict")

    def test_deploy_ready_packages_copies_only_to_empty_game_mods_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            source = root / "incoming"
            source.mkdir()
            (source / "package.json").write_text(json.dumps({"id": "deploy.mod", "name": "Deploy", "version": "1.0"}))
            (source / "mod.lua").write_text("return {}")
            service = PackageService(root, profiles)
            package = service.install_from_directory(source)
            profile = service.set_enabled(profiles.list()[0], package.id, True)
            game = root / "game"
            game.mkdir()
            deployed = service.deploy_ready(profile, game)
            self.assertEqual(deployed[0].status, "ready")
            self.assertTrue((game / "mods" / package.id / "mod.lua").exists())
            self.assertTrue((game / "mods" / package.id / ".embervault-managed.json").exists())
            marker = json.loads((game / "mods" / package.id / ".embervault-managed.json").read_text())
            self.assertEqual(marker["marker_version"], 1)
            self.assertEqual(marker["package_version"], package.version)
            service.undeploy(package.id, game)
            self.assertFalse((game / "mods" / package.id).exists())
            service.deploy_ready(profile, game)
            (game / "mods" / package.id / "user-file.txt").write_text("existing")
            (game / "mods" / package.id / ".embervault-managed.json").write_text(json.dumps({"package_id": "other"}))
            with self.assertRaises(ValueError):
                service.undeploy(package.id, game)

    def test_deployment_inspection_distinguishes_managed_external_and_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mods = root / "game" / "mods"
            (mods / "external.mod").mkdir(parents=True)
            invalid = mods / "invalid.mod"
            invalid.mkdir()
            (invalid / ".embervault-managed.json").write_text(json.dumps({"package_id": "invalid.mod"}))
            managed = mods / "managed.mod"
            managed.mkdir()
            (managed / ".embervault-managed.json").write_text(json.dumps({
                "marker_version": 1, "package_id": "managed.mod", "package_version": "1.0",
                "managed_by": "embervault-control-center",
            }))
            service = PackageService(root, ProfileService(root))
            findings = service.inspect_deployments(root / "game")
            self.assertEqual({item.status for item in findings}, {"external", "unsafe", "managed"})

    def test_failed_copy_removes_partial_current_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "package.json").write_text(json.dumps({"id": "partial.mod", "name": "Partial", "version": "1.0"}))
            (incoming / "mod.lua").write_text("return {}")
            service = PackageService(root, profiles)
            package = service.install_from_directory(incoming)
            profile = service.set_enabled(profiles.list()[0], package.id, True)
            game = root / "game"
            game.mkdir()
            destination = game / "mods" / package.id

            def partial_copy(_source, target):
                Path(target).mkdir(parents=True)
                (Path(target) / "partial.txt").write_text("incomplete")
                raise OSError("simulated interrupted copy")

            with mock.patch("core.packages.shutil.copytree", side_effect=partial_copy):
                with self.assertRaises(OSError):
                    service.deploy_ready(profile, game)
            self.assertFalse(destination.exists())

    def test_deployment_plan_marks_missing_source_as_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            source = root / "incoming"
            source.mkdir()
            (source / "package.json").write_text(json.dumps({"id": "gone.mod", "name": "Gone", "version": "1.0"}))
            service = PackageService(root, profiles)
            package = service.install_from_directory(source)
            profile = service.set_enabled(profiles.list()[0], package.id, True)
            shutil.rmtree(root / "packages" / package.id)
            service._packages[package.id] = package
            self.assertEqual(service.deployment_plan(profile, root / "game")[0].status, "missing")

    def test_deploy_ready_rejects_missing_game_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            service = PackageService(root, profiles)
            with self.assertRaises(ValueError):
                service.deploy_ready(profiles.list()[0], root / "not-a-game")

    def test_deployment_plan_keeps_non_mod_packages_out_of_game_mods(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            source = root / "incoming"
            source.mkdir()
            (source / "package.json").write_text(json.dumps({
                "id": "tuning.test", "name": "Tuning", "version": "1.0", "package_type": "tuning",
            }))
            service = PackageService(root, profiles)
            package = service.install_from_directory(source)
            profile = service.set_enabled(profiles.list()[0], package.id, True)
            game = root / "game"
            game.mkdir()
            plan = service.deployment_plan(profile, game)
            self.assertEqual(plan[0].status, "unsupported")
            with self.assertRaises(ValueError):
                service.deploy_ready(profile, game)

    def test_deployment_plan_blocks_symlinked_package_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            source = root / "incoming"
            source.mkdir()
            (source / "package.json").write_text(json.dumps({"id": "link.mod", "name": "Link", "version": "1.0"}))
            service = PackageService(root, profiles)
            package = service.install_from_directory(source)
            profile = service.set_enabled(profiles.list()[0], package.id, True)
            target = root / "packages" / package.id / "outside.txt"
            outside = root / "outside.txt"
            outside.write_text("outside")
            target.symlink_to(outside)
            service._packages[package.id] = package
            self.assertEqual(service.deployment_plan(profile, root / "game")[0].status, "unsafe")

    def test_clean_package_service_can_discover_seed_example(self):
        with tempfile.TemporaryDirectory() as temp:
            profiles = ProfileService(Path(temp))
            profiles.ensure_defaults()
            packages = PackageService(Path(temp), profiles)
            self.assertEqual([item.id for item in packages.list()], ["embervault.eml-tuning-adapter", "embervault.example-mod"])

    def test_package_discovery_merges_seed_and_runtime_packages(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            (root / "packages").mkdir()
            service = PackageService(root, profiles)
            self.assertEqual([item.id for item in service.list()], ["embervault.eml-tuning-adapter", "embervault.example-mod"])
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "package.json").write_text(json.dumps({"id": "local.mod", "name": "Local", "version": "1.0.0"}))
            service.install_from_directory(incoming)
            self.assertEqual({item.id for item in service.list()}, {"embervault.eml-tuning-adapter", "embervault.example-mod", "local.mod"})

    def test_managed_package_cannot_be_removed_while_enabled(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "package.json").write_text(json.dumps({"id": "managed.mod", "name": "Managed", "version": "1.0.0"}))
            packages = PackageService(root, profiles)
            packages.install_from_directory(incoming)
            default = profiles.list()[0]
            packages.set_enabled(default, "managed.mod", True)
            with self.assertRaises(ValueError):
                packages.remove("managed.mod")
            packages.set_enabled(default, "managed.mod", False)
            packages.remove("managed.mod")
            self.assertIsNone(packages.get("managed.mod"))

    def test_package_removal_rejects_symlinked_managed_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            source = root / "incoming"
            source.mkdir()
            (source / "package.json").write_text(json.dumps({"id": "linked.mod", "name": "Linked", "version": "1.0"}))
            packages = PackageService(root, profiles)
            packages.install_from_directory(source)
            target = root / "packages" / "linked.mod"
            backup = root / "linked-target"
            target.rename(backup)
            try:
                target.symlink_to(backup, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            packages.discover()
            with self.assertRaisesRegex(ValueError, "Unknown installed package"):
                packages.remove("linked.mod")

    def test_package_folder_import_rejects_symlinked_source_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            source = root / "incoming"
            source.mkdir()
            (source / "package.json").write_text(json.dumps({"id": "linked.mod", "name": "Linked", "version": "1.0"}))
            outside = root / "outside.txt"
            outside.write_text("outside")
            try:
                (source / "link.txt").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "symlink"):
                PackageService(root, profiles).install_from_directory(source)

    def test_package_discovery_ignores_symlinked_package_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            packages_dir = root / "packages"
            packages_dir.mkdir()
            outside = root / "outside-package"
            outside.mkdir()
            (outside / "package.json").write_text(json.dumps({"id": "outside.mod", "name": "Outside", "version": "1.0"}))
            try:
                (packages_dir / "outside.mod").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            self.assertNotIn("outside.mod", PackageService(root, profiles).discover())

    def test_package_removal_protects_dependents(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "package.json").write_text(json.dumps({
                "id": "base.mod", "name": "Base", "version": "1.0",
            }))
            packages = PackageService(root, profiles)
            packages.install_from_directory(incoming)
            dependent = root / "dependent"
            dependent.mkdir()
            (dependent / "package.json").write_text(json.dumps({
                "id": "addon.mod", "name": "Addon", "version": "1.0", "dependencies": ["base.mod"],
            }))
            packages.install_from_directory(dependent)
            with self.assertRaisesRegex(ValueError, "dependent"):
                packages.remove("base.mod")

    def test_package_archive_import_rejects_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            archive = root / "unsafe.zip"
            import zipfile
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("../escape.txt", "no")
            with self.assertRaises(ValueError):
                PackageService(root, profiles).install_from_archive(archive)

    def test_package_archive_rejects_windows_traversal_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            archive = root / "windows-unsafe.zip"
            import zipfile
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("..\\outside.txt", "unsafe")
            with self.assertRaises(ValueError):
                PackageService(root, profiles).install_from_archive(archive)

    def test_package_archive_rejects_symlink_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            archive = root / "symlink.zip"
            import zipfile
            info = zipfile.ZipInfo("package/link")
            info.external_attr = (0o120777 << 16) | 0xA000
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr(info, "../../outside")
            with self.assertRaises(ValueError):
                PackageService(root, profiles).install_from_archive(archive)

    def test_package_archive_rejects_duplicate_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            archive = root / "duplicate.zip"
            import zipfile
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("package/package.json", "{}")
                bundle.writestr("package/package.json", "{\"id\": \"different.mod\"}")
            with self.assertRaises(ValueError):
                PackageService(root, profiles).install_from_archive(archive)

    def test_package_archive_rejects_excessive_entry_count(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            archive = root / "too-many.zip"
            import zipfile
            with zipfile.ZipFile(archive, "w") as bundle:
                for index in range(2049):
                    bundle.writestr(f"package/file-{index}.txt", "x")
            with self.assertRaises(ValueError):
                PackageService(root, profiles).install_from_archive(archive)

    def test_package_archive_imports_nested_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            archive = root / "package.zip"
            import zipfile
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("demo/package.json", json.dumps({"id": "archive.mod", "name": "Archive", "version": "1.0.0"}))
            package = PackageService(root, profiles).install_from_archive(archive)
            self.assertEqual(package.id, "archive.mod")

    def test_package_archive_rejects_multiple_package_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            archive = root / "ambiguous.zip"
            import zipfile
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("first/package.json", json.dumps({"id": "first.mod", "name": "First", "version": "1.0.0"}))
                bundle.writestr("second/package.json", json.dumps({"id": "second.mod", "name": "Second", "version": "1.0.0"}))
            with self.assertRaisesRegex(ValueError, "multiple package roots"):
                PackageService(root, profiles).install_from_archive(archive)

    def test_package_manifest_rejects_path_like_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "package.json").write_text(json.dumps({"id": "../escape", "name": "Unsafe", "version": "1.0.0"}))
            with self.assertRaises(ValueError):
                PackageService(root, profiles).install_from_directory(incoming)

    def test_package_manifest_rejects_path_like_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "package.json").write_text(json.dumps({
                "id": "unsafe.mod", "name": "Unsafe", "version": "1.0", "dependencies": ["../escape"],
            }))
            with self.assertRaises(ValueError):
                PackageService(root, profiles).install_from_directory(incoming)

    def test_package_manifest_rejects_duplicate_or_self_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            for dependencies in (["base.mod", "base.mod"], ["self.mod"]):
                incoming = root / ("incoming-" + str(len(dependencies)))
                incoming.mkdir()
                package_id = "self.mod" if dependencies == ["self.mod"] else "duplicate.mod"
                (incoming / "package.json").write_text(json.dumps({
                    "id": package_id, "name": "Invalid", "version": "1.0", "dependencies": dependencies,
                }))
                with self.assertRaises(ValueError):
                    PackageService(root, profiles).install_from_directory(incoming)

    def test_package_manifest_requires_array_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "package.json").write_text(json.dumps({
                "id": "bad-shape.mod", "name": "Bad", "version": "1.0", "dependencies": "base.mod",
            }))
            with self.assertRaises(ValueError):
                PackageService(root, profiles).install_from_directory(incoming)

    def test_package_manifest_rejects_blank_required_builds(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            package.mkdir()
            (package / "package.json").write_text(json.dumps({
                "id": "test.mod", "name": "Test", "version": "1.0",
                "required_builds": [" 123 ", "", "  "],
            }))
            with self.assertRaises(ValueError):
                PackageManifest.from_file(package / "package.json")

    def test_package_manifest_rejects_weak_optional_types_and_duplicate_builds(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            package.mkdir()
            cases = [
                {"id": "typed.mod", "name": "Typed", "version": "1.0", "author": 7},
                {"id": "typed.mod", "name": "Typed", "version": "1.0", "description": None},
                {"id": "typed.mod", "name": "Typed", "version": "1.0", "required_builds": ["1", "1"]},
            ]
            for index, payload in enumerate(cases):
                manifest = package / f"manifest-{index}.json"
                manifest.write_text(json.dumps(payload))
                with self.assertRaises(ValueError):
                    PackageManifest.from_file(manifest)

    def test_package_manifest_rejects_non_string_build_or_dependency_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            package.mkdir()
            (package / "package.json").write_text(json.dumps({
                "id": "test.mod", "name": "Test", "version": "1.0",
                "required_builds": [123], "dependencies": ["base.mod"],
            }))
            with self.assertRaises(ValueError):
                PackageManifest.from_file(package / "package.json")

    def test_package_manifest_requires_string_identity_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            package.mkdir()
            (package / "package.json").write_text(json.dumps({
                "id": "test.mod", "name": 12, "version": "1.0",
            }))
            with self.assertRaises(ValueError):
                PackageManifest.from_file(package / "package.json")

    def test_package_manifest_requires_non_empty_package_type(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package"
            package.mkdir()
            (package / "package.json").write_text(json.dumps({
                "id": "test.mod", "name": "Test", "version": "1.0", "package_type": "  ",
            }))
            with self.assertRaises(ValueError):
                PackageManifest.from_file(package / "package.json")

    def test_package_enablement_blocks_known_incompatible_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "package.json").write_text(json.dumps({
                "id": "build.mod", "name": "Build Mod", "version": "1.0.0", "required_builds": ["old"]
            }))
            packages = PackageService(root, profiles)
            packages.install_from_directory(incoming)
            with self.assertRaises(ValueError):
                packages.set_enabled(profiles.list()[0], "build.mod", True, "new")

    def test_package_enablement_requires_profile_dependencies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            for package_id, dependencies in (("base.mod", []), ("addon.mod", ["base.mod"])):
                package = root / "packages" / package_id
                package.mkdir(parents=True)
                (package / "package.json").write_text(json.dumps({
                    "id": package_id, "name": package_id, "version": "1.0", "dependencies": dependencies,
                }))
            packages = PackageService(root, profiles)
            packages.discover()
            profile = profiles.list()[0]
            with self.assertRaisesRegex(ValueError, "dependencies"):
                packages.set_enabled(profile, "addon.mod", True)
            profile = packages.set_enabled(profile, "base.mod", True)
            profile = packages.set_enabled(profile, "addon.mod", True)

    def test_package_disable_protects_enabled_dependents(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            for package_id, dependencies in (("base.mod", []), ("addon.mod", ["base.mod"])):
                package = root / "packages" / package_id
                package.mkdir(parents=True)
                (package / "package.json").write_text(json.dumps({
                    "id": package_id, "name": package_id, "version": "1.0", "dependencies": dependencies,
                }))
            packages = PackageService(root, profiles)
            packages.discover()
            profile = profiles.list()[0]
            profile = packages.set_enabled(profile, "base.mod", True)
            profile = packages.set_enabled(profile, "addon.mod", True)
            with self.assertRaisesRegex(ValueError, "Disable dependent"):
                packages.set_enabled(profile, "base.mod", False)

    def test_deployment_plan_carries_profile_and_blocks_incompatible_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = ProfileService(root)
            profiles.ensure_defaults()
            package = root / "packages" / "build.mod"
            package.mkdir(parents=True)
            (package / "package.json").write_text(json.dumps({
                "id": "build.mod", "name": "Build Mod", "version": "1.0",
                "required_builds": ["old-build"],
            }))
            service = PackageService(root, profiles)
            service.discover()
            profile = service.set_enabled(profiles.list()[0], "build.mod", True)
            plan = service.deployment_plan(profile, root / "game", detected_build="new-build")
            self.assertEqual(plan[0].profile_id, profile.id)
            self.assertEqual(plan[0].compatibility_state, "incompatible")
            self.assertEqual(plan[0].status, "incompatible")

    def test_package_graph_profile_compare_and_batch_enablement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); profiles = ProfileService(root); profiles.ensure_defaults()
            for package_id, dependencies in (("base.mod", []), ("addon.mod", ["base.mod"])):
                folder = root / "packages" / package_id; folder.mkdir(parents=True)
                (folder / "package.json").write_text(json.dumps({"id": package_id, "name": package_id, "version": "1", "dependencies": dependencies}))
            service = PackageService(root, profiles); service.discover(); profile = profiles.list()[0]
            updated = service.batch_set_enabled(profile, ["base.mod", "addon.mod"], True)
            other = Profile("other", "Other", enabled_packages=["base.mod"])
            comparison = service.compare_profiles(updated, other)
            self.assertEqual(service.dependency_graph()["addon.mod"], ["base.mod"])
            self.assertEqual(comparison["only_left"], ["addon.mod"])

    def test_package_update_detection_and_profile_portability(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); profiles = ProfileService(root); profiles.ensure_defaults()
            folder = root / "packages" / "demo.mod"; folder.mkdir(parents=True)
            (folder / "package.json").write_text(json.dumps({"id": "demo.mod", "name": "Demo", "version": "1.0.0"}))
            packages = PackageService(root, profiles); packages.discover()
            self.assertEqual(packages.update_candidates([{"id": "demo.mod", "version": "1.1.0"}])[0]["available"], "1.1.0")
            exported = profiles.export_profile("default", root / "default.json")
            imported = profiles.import_profile(exported, new_id="copied")
            self.assertEqual(imported.id, "copied")

    def test_package_upgrade_is_staged_without_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); profiles = ProfileService(root); profiles.ensure_defaults()
            installed = root / "packages" / "demo.mod"; installed.mkdir(parents=True)
            (installed / "package.json").write_text(json.dumps({"id": "demo.mod", "name": "Demo", "version": "1.0.0"}))
            incoming = root / "incoming"; incoming.mkdir()
            (incoming / "package.json").write_text(json.dumps({"id": "demo.mod", "name": "Demo", "version": "1.1.0"}))
            service = PackageService(root, profiles); service.discover()
            result = service.stage_upgrade(incoming)
            self.assertTrue(result["requires_review"])
            self.assertFalse(result["replacement_performed"])
            self.assertEqual(service.get("demo.mod").version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
