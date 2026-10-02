import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock
from pathlib import Path

from core.application import EmbervaultRuntime
from core.operations import OperationStatus
from core.integration import IntegrationContext
from core.promotion import PromotionEvidence
from control_center.backend import ControlCenterBackend


class ApplicationCompositionTests(unittest.TestCase):
    def test_promotion_requires_all_lifecycle_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            evidence = PromotionEvidence("embervault.eml", "1076226", True, True, True, True, "EmberVault", True)
            decision = runtime.promotion.promote(evidence, "verified")
            self.assertEqual(decision["target_state"], "verified")
            self.assertEqual(runtime.catalog.build()["promotions"][0]["target_state"], "verified")
            with self.assertRaises(ValueError):
                runtime.promotion.promote(PromotionEvidence("x", "1076226", True, False, True, True, "owner", True), "stable")
            self.assertEqual(runtime.promotion.approved_state("embervault.eml"), "verified")
    def test_runtime_composes_services_and_reports_health(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            health = runtime.health()
            self.assertEqual(health["core"], "ready")
            self.assertEqual(health["profiles"], 2)
            self.assertEqual(health["modules"], 5)
            self.assertEqual(health["backups"], 0)
            self.assertEqual(health["research"], 0)
            self.assertEqual(health["knowledge"], 8)
            self.assertEqual(health["content_projects"], 0)
            self.assertEqual(health["trainer_plans"], 0)

    def test_backend_exposes_workspace_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            self.assertIn("Research · 0 records", backend.workspaceSummary)
            self.assertIn("Knowledge · 8 entries", backend.workspaceSummary)
            self.assertIn("Content · 0 projects", backend.workspaceSummary)
            self.assertIn("Trainer · 0 plans", backend.workspaceSummary)

    def test_backend_reports_adapter_lifecycle_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            runtime = EmbervaultRuntime.create(root)
            backend = ControlCenterBackend(root, runtime=runtime)
            self.assertIn("not staged", backend.tuningAdapterStatus)

    def test_backend_recovers_staged_adapter_from_operation_history(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            runtime = EmbervaultRuntime.create(root)
            package = root / "staging" / "EV-OP-RECOVER-eml-tuning-adapter"
            package.mkdir(parents=True)
            operation = runtime.operations.start("tuning-adapter-stage", profile_id="research")
            runtime.operations.finish(operation, OperationStatus.SUCCEEDED, f"Staged EML adapter payload at {package}")
            recovered = ControlCenterBackend(root, runtime=EmbervaultRuntime.create(root))
            self.assertEqual(recovered._staged_adapter_package, package)
            self.assertEqual(recovered._staged_adapter_operation_id, operation.id)

    def test_backend_recovers_deployed_adapter_state_from_operation_history(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            runtime = EmbervaultRuntime.create(root)
            operation = runtime.operations.start("tuning-adapter-deploy", profile_id="research")
            runtime.operations.finish(operation, OperationStatus.SUCCEEDED, "Deployed owned EML adapter")
            recovered = ControlCenterBackend(root, runtime=EmbervaultRuntime.create(root))
            self.assertTrue(recovered._adapter_deployed)
            self.assertIn("deployed; launch verification pending", recovered.tuningAdapterStatus)

    def test_backend_honors_adapter_rollback_as_terminal_recovery_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = EmbervaultRuntime.create(root)
            staged = root / "staging" / "EV-OP-ROLLBACK-eml-tuning-adapter"
            staged.mkdir(parents=True)
            stage = runtime.operations.start("tuning-adapter-stage", profile_id="research")
            runtime.operations.finish(stage, OperationStatus.SUCCEEDED, f"Staged EML adapter payload at {staged}")
            deploy = runtime.operations.start("tuning-adapter-deploy", profile_id="research")
            runtime.operations.finish(deploy, OperationStatus.SUCCEEDED, "Deployed owned EML adapter")
            rollback = runtime.operations.start("tuning-adapter-rollback", profile_id="research")
            runtime.operations.finish(rollback, OperationStatus.SUCCEEDED, "Removed owned EML adapter")
            recovered = ControlCenterBackend(root, runtime=EmbervaultRuntime.create(root))
            self.assertIsNone(recovered._staged_adapter_package)
            self.assertIsNone(recovered._staged_adapter_operation_id)
            self.assertFalse(recovered._adapter_deployed)

    def test_backend_recovers_verified_adapter_state_from_operation_history(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            runtime = EmbervaultRuntime.create(root)
            deploy = runtime.operations.start("tuning-adapter-deploy", profile_id="research")
            runtime.operations.finish(deploy, OperationStatus.SUCCEEDED, "Deployed owned EML adapter")
            verify = runtime.operations.start("tuning-adapter-verify", profile_id="research")
            runtime.operations.finish(verify, OperationStatus.SUCCEEDED, "Verified EML readback")
            recovered = ControlCenterBackend(root, runtime=EmbervaultRuntime.create(root))
            self.assertTrue(recovered._adapter_verified)
            self.assertIn("verified", recovered.tuningAdapterStatus)

    def test_backend_requires_deployment_before_adapter_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = EmbervaultRuntime.create(root)
            backend = ControlCenterBackend(root, runtime=runtime)
            backend._staged_adapter_operation_id = "EV-OP-STAGED"
            backend.settings.game_path = str(root / "game")
            self.assertFalse(backend.canVerifyTuningAdapter)
            self.assertEqual(backend.verifyTuningAdapter(), "Deploy the staged EML adapter first")

    def test_backend_rolls_back_owned_adapter_after_failed_readback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            runtime = EmbervaultRuntime.create(root)
            backend = ControlCenterBackend(root, runtime=runtime)
            game = root / "game"
            destination = game / "mods" / "embervault.eml-tuning-adapter"
            destination.mkdir(parents=True)
            (destination / ".embervault-managed.json").write_text(
                json.dumps({"package_id": "embervault.eml-tuning-adapter", "managed_by": "embervault-control-center"}),
                encoding="utf-8",
            )
            (game / "logs").mkdir(parents=True)
            (game / "logs" / "current.eml.log").write_text("unrelated runtime output", encoding="utf-8")
            backend.settings.game_path = str(game)
            backend._staged_adapter_operation_id = "EV-OP-FAIL"
            backend._adapter_deployed = True
            backend._adapter_deployed_at = 0.0
            message = backend.verifyTuningAdapter()
            self.assertIn("EML verification failed", message)
            self.assertIn("rolled back", message)
            self.assertFalse(destination.exists())
            self.assertFalse(backend._adapter_deployed)
            self.assertTrue(any(item.operation_type == "tuning-adapter-verify" and item.status == OperationStatus.FAILED
                                for item in runtime.operations.list_recent()))

    def test_backend_exposes_selected_profile_index(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            self.assertEqual(backend.selectedProfileIndex, 0)
            backend.selectProfile(1)
            self.assertEqual(backend.selectedProfileIndex, 1)

    def test_backend_imports_staged_settings_for_selected_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = EmbervaultRuntime.create(root)
            backend = ControlCenterBackend(root, runtime=runtime)
            profile = runtime.profiles.list()[0]
            manifest = root / "settings.json"
            manifest.write_text(json.dumps({
                "schema_version": 1,
                "profile_id": profile.id,
                "application_state": "staged-only",
                "settings": {
                    "enemy_damage_multiplier": 1.25,
                    "resource_yield_multiplier": 1.0,
                    "experimental_rules": False,
                    "base_crit_chance": 0.1,
                },
            }), encoding="utf-8")
            backend.importGameSettings(str(manifest))
            self.assertIn("Imported staged settings", backend.lastSaveMessage)
            selected = next(item for item in backend.profiles if item.id == profile.id)
            self.assertEqual(selected.settings["enemy_damage_multiplier"], 1.25)
            self.assertEqual(backend.operations.list_recent(1)[0].operation_type, "game-settings-import")

    def test_backend_requires_restore_preview_before_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend._selected_backup_id = "unpreviewed"
            backend._save_directory = temp
            backend.restoreSelected()
            self.assertIn("Preview the selected restore", backend.lastSaveMessage)
            self.assertFalse(backend.canRestore)

    def test_troubleshooter_reports_unconfigured_game_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            findings = runtime.troubleshooter.scan()
            self.assertEqual(findings[0].key, "game-path")
            self.assertEqual(findings[0].severity, "attention")

    def test_research_record_keeps_evidence_with_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Yield test", "Yield changes under staged setting", "research")
            updated = runtime.research.add_evidence(record.id, "Observed baseline behavior")
            self.assertEqual(updated.profile_id, "research")
            self.assertEqual(updated.evidence, ["Observed baseline behavior"])

    def test_research_summary_export_excludes_profile_and_evidence_text(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Yield test", "Test staged yield", "research")
            runtime.research.add_evidence(record.id, "Private observation")
            destination = runtime.research.export_summary(runtime.research.list()[0])
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(payload["application_state"], "research-summary")
            self.assertEqual(payload["record"]["evidence_count"], 1)
            self.assertNotIn("profile_id", payload["record"])
            self.assertNotIn("Private observation", destination.read_text(encoding="utf-8"))

    def test_research_record_tracks_reproduction_failures_and_promotion_review(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Build study", "The change is reproducible", "research", "1076226", "0.1")
            runtime.research.add_reproduction_step(record.id, "Start from a clean research profile")
            runtime.research.add_failure(record.id, "First run lacked the expected log evidence")
            runtime.research.add_evidence(record.id, "Second run reproduced the observation")
            runtime.research.set_status(record.id, "completed")
            requested = runtime.research.set_promotion_review(record.id, "requested", "Review adapter boundary")
            self.assertEqual(requested.game_build, "1076226")
            self.assertEqual(requested.reproduction_steps, ["Start from a clean research profile"])
            self.assertEqual(requested.failures, ["First run lacked the expected log evidence"])
            approved = runtime.research.set_promotion_review(record.id, "approved", "Evidence is sufficient")
            self.assertEqual(approved.promotion_status, "approved")
            linked = runtime.research.link_context(record.id, ["embervault.example-mod"], ["embervault.research"], ["save-safety"])
            self.assertEqual(linked.linked_package_ids, ["embervault.example-mod"])
            exported = runtime.research.export_summary(linked)
            payload = json.loads(exported.read_text(encoding="utf-8"))
            self.assertEqual(payload["record"]["reproduction_step_count"], 1)
            self.assertEqual(payload["record"]["failure_count"], 1)
            self.assertEqual(payload["record"]["linked_module_count"], 1)
            self.assertNotIn("clean research profile", exported.read_text(encoding="utf-8"))

    def test_research_context_changes_retract_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Public study", "Documented", "research")
            runtime.research.add_reproduction_step(record.id, "Repeat the observation")
            runtime.research.add_evidence(record.id, "Observed")
            runtime.research.set_status(record.id, "completed")
            published = runtime.research.publish(record.id)
            self.assertTrue(published.published)
            changed = runtime.research.link_context(record.id, modules=["embervault.research"])
            self.assertFalse(changed.published)
            self.assertEqual(runtime.catalog.build()["research"], [])

    def test_knowledge_catalog_searches_seeded_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            entries = runtime.knowledge.search("restore")
            self.assertEqual([entry.id for entry in entries], ["save-safety"])

    def test_knowledge_entry_creation_preserves_seeded_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            seeded_count = len(runtime.knowledge.entries())
            entry = runtime.knowledge.create("Local Finding", "Research", "A local summary", "Observed during a safe probe.")
            self.assertEqual(len(runtime.knowledge.entries()), seeded_count + 1)
            self.assertEqual(runtime.knowledge.search("safe probe")[0].id, entry.id)

    def test_knowledge_entry_supports_metadata_and_private_version_history(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            entry = runtime.knowledge.create("Linked finding", "Research", "A finding", "First draft",
                                              ["safety", "research"], ["save-safety"], ["EV-RES-1"])
            updated = runtime.knowledge.update(entry.id, "Linked finding", "Research", "A revised finding", "Second draft",
                                                ["research"], ["save-safety", "profiles"], ["EV-RES-2"])
            self.assertEqual(updated.version, 2)
            self.assertEqual(updated.tags, ("research",))
            self.assertEqual(len(updated.history), 1)
            self.assertFalse(updated.published)
            runtime.knowledge.publish(updated.id)
            public = runtime.catalog.build()["knowledge"]
            record = next(item for item in public if item["id"] == entry.id)
            self.assertEqual(record["version"], 2)
            self.assertEqual(record["related_ids"], ["profiles", "save-safety"])
            self.assertNotIn("First draft", json.dumps(public))
            self.assertNotIn("history", json.dumps(public))
            self.assertIn(entry.id, [item.id for item in runtime.knowledge.search("safety")])
            self.assertIn(entry.id, [item.id for item in runtime.knowledge.search("EV-RES-2")])

    def test_local_knowledge_requires_explicit_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            entry = runtime.knowledge.create("Private Finding", "Research", "Private summary", "Private observation")
            self.assertNotIn(entry.id, [item["id"] for item in runtime.catalog.build()["knowledge"]])
            runtime.knowledge.publish(entry.id)
            self.assertIn(entry.id, [item["id"] for item in runtime.catalog.build()["knowledge"]])
            runtime.knowledge.unpublish(entry.id)
            self.assertNotIn(entry.id, [item["id"] for item in runtime.catalog.build()["knowledge"]])

    def test_troubleshooter_flags_package_with_unsupported_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = EmbervaultRuntime.create(root)
            package = root / "packages" / "tested"
            package.mkdir(parents=True)
            (package / "package.json").write_text(
                '{"id":"tested.mod","name":"Tested Mod","version":"1.0.0","required_builds":["old-build"]}'
            )
            game = root / "game" / "steamapps"
            game.mkdir(parents=True)
            (game.parent / "Enshrouded.exe").write_bytes(b"")
            (game / "appmanifest_1203620.acf").write_text('"buildid" "123"')
            runtime.settings.save(type(runtime.settings.load())(game_path=str(game.parent)))
            findings = runtime.troubleshooter.scan()
            self.assertTrue(any(item.key == "package-tested.mod" for item in findings))

    def test_troubleshooter_flags_deployment_conflict(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = EmbervaultRuntime.create(root)
            source = root / "incoming"
            source.mkdir()
            (source / "package.json").write_text(json.dumps({"id": "conflict.mod", "name": "Conflict", "version": "1.0"}))
            package = runtime.packages.install_from_directory(source)
            profile = runtime.profiles.list()[0]
            runtime.packages.set_enabled(profile, package.id, True)
            game = root / "game"
            (game / "mods" / package.id).mkdir(parents=True)
            runtime.settings.save(type(runtime.settings.load())(game_path=str(game)))
            findings = runtime.troubleshooter.scan()
            self.assertTrue(any(item.key == "deployment-default-conflict.mod" for item in findings))

    def test_game_detection_treats_malformed_manifest_as_unknown_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            steamapps = root / "steamapps"
            steamapps.mkdir()
            (steamapps / "appmanifest_1203620.acf").write_text('"buildid" "not-a-number"')
            installation = EmbervaultRuntime.create(Path(temp)).game.detect(root)
            self.assertIsNone(installation.build_id)

    def test_game_detection_reports_missing_build_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Enshrouded.exe").write_bytes(b"")
            runtime = EmbervaultRuntime.create(Path(temp))
            installation = runtime.game.detect(root)
            self.assertIn("build evidence", " ".join(runtime.game.validate(installation)).lower())

    def test_troubleshooter_flags_missing_package_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = EmbervaultRuntime.create(root)
            package = root / "packages" / "addon.mod"
            package.mkdir(parents=True)
            (package / "package.json").write_text(json.dumps({
                "id": "addon.mod", "name": "Addon", "version": "1.0", "dependencies": ["missing.mod"],
            }))
            findings = runtime.troubleshooter.scan()
            self.assertTrue(any(item.key == "package-dependency-addon.mod" for item in findings))

    def test_troubleshooter_flags_package_dependency_cycle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = EmbervaultRuntime.create(root)
            for package_id, dependency in (("alpha.mod", "beta.mod"), ("beta.mod", "alpha.mod")):
                package = root / "packages" / package_id
                package.mkdir(parents=True)
                (package / "package.json").write_text(json.dumps({
                    "id": package_id, "name": package_id, "version": "1.0", "dependencies": [dependency],
                }))
            findings = runtime.troubleshooter.scan()
            self.assertTrue(any(item.key == "package-dependency-cycle" for item in findings))

    def test_catalog_export_excludes_local_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            export = runtime.catalog.build()
            self.assertEqual(export["schema_version"], 1)
            self.assertEqual(export["contract_versions"]["package_manifest"], 1)
            self.assertEqual(export["contract_versions"]["integration_context"], 1)
            self.assertIn("knowledge", export)
            self.assertTrue(all(item["path"] is None for item in export["modules"]))

    def test_catalog_export_includes_sanitized_research_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Yield study", "Observe yield", "research")
            runtime.research.add_evidence(record.id, "private local observation")
            self.assertEqual(runtime.catalog.build()["research"], [])
            runtime.research.set_status(record.id, "completed")
            runtime.research.publish(record.id)
            research = runtime.catalog.build()["research"]
            self.assertEqual(research[0]["evidence_count"], 1)
            self.assertNotIn("private local observation", json.dumps(research))
            self.assertNotIn("profile_id", research[0])
            self.assertEqual(set(research[0]), {"id", "title", "hypothesis", "status", "evidence_count", "created_at", "published_at", "game_build", "game_version", "reproduction_step_count", "failure_count", "promotion_status", "linked_package_count", "linked_module_count", "linked_knowledge_count"})
            self.assertTrue(research[0]["published_at"])

    def test_research_publish_requires_completion_and_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Private", "Do not publish yet", "research")
            with self.assertRaises(ValueError):
                runtime.research.publish(record.id)

    def test_research_can_be_unpublished_without_losing_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Public", "Documented", "research")
            runtime.research.add_evidence(record.id, "Observed")
            runtime.research.set_status(record.id, "completed")
            published = runtime.research.publish(record.id)
            unpublished = runtime.research.unpublish(record.id)
            self.assertTrue(published.published)
            self.assertFalse(unpublished.published)
            self.assertEqual(unpublished.published_at, "")
            self.assertEqual(unpublished.evidence, ["Observed"])
            self.assertEqual(runtime.catalog.build()["research"], [])

    def test_research_options_show_private_or_published_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = EmbervaultRuntime.create(root)
            record = runtime.research.create("Visible", "Documented", "research")
            runtime.research.add_evidence(record.id, "Observed")
            runtime.research.set_status(record.id, "completed")
            backend = ControlCenterBackend(root, runtime=runtime)
            backend.selectProfile(1)
            self.assertIn("PRIVATE", backend.researchOptions[0])
            runtime.research.publish(record.id)
            self.assertIn("PUBLISHED", backend.researchOptions[0])

    def test_published_research_retracts_when_evidence_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Mutable", "Documented", "research")
            runtime.research.add_evidence(record.id, "Initial")
            runtime.research.set_status(record.id, "completed")
            runtime.research.publish(record.id)
            updated = runtime.research.add_evidence(record.id, "Correction")
            self.assertFalse(updated.published)
            self.assertEqual(updated.published_at, "")
            self.assertEqual(runtime.catalog.build()["research"], [])

    def test_catalog_export_writes_json_document(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            destination = runtime.catalog.export(Path(temp) / "out" / "catalog.json")
            self.assertTrue(destination.is_file())
            self.assertIn('"schema_version": 1', destination.read_text(encoding="utf-8"))
            self.assertIn('"generated_at":', destination.read_text(encoding="utf-8"))

    def test_catalog_declares_tuning_adapter_contract_version(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            self.assertEqual(runtime.catalog.build()["contract_versions"]["tuning_adapter"], 1)

    def test_catalog_exposes_sanitized_tuning_adapter_record_when_manifest_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            catalog = EmbervaultRuntime.create(root).catalog.build()
            self.assertEqual(len(catalog["tuning_adapters"]), 1)
            record = catalog["tuning_adapters"][0]
            self.assertEqual(record["loader"], "EML")
            self.assertEqual(record["supported_setting_keys"], ["baseCritChance"])
            self.assertNotIn("source", record)
            self.assertNotIn("mutation_scope", record)

    def test_catalog_sanitizes_internal_module_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            catalog = EmbervaultRuntime.create(Path(temp)).catalog.build()
            module = next(item for item in catalog["modules"] if item["id"] == "embervault.example")
            self.assertNotIn("safety", module)
            self.assertNotIn("recovery", module)
            self.assertNotIn("operation_types", module)

    def test_eml_tuning_adapter_loads_existing_reversible_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            from core.tuning_adapter import TuningAdapterService
            manifest = TuningAdapterService(root).manifest()
            self.assertEqual(manifest["supported_setting_keys"], ["baseCritChance"])

    def test_eml_tuning_adapter_rejects_runtime_build_or_api_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            from core.tuning_adapter import TuningAdapterService
            service = TuningAdapterService(root)
            self.assertEqual(service.validate_runtime_context(loader="EML", loader_api_version="1.3", game_build="1076226")["game_build"], "1076226")
            with self.assertRaises(ValueError):
                service.validate_runtime_context(loader="EML", loader_api_version="1.2", game_build="1076226")
            with self.assertRaises(ValueError):
                service.validate_runtime_context(loader="EML", loader_api_version="1.3", game_build="other")

    def test_eml_tuning_adapter_prepares_preview_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            from core.tuning_adapter import TuningAdapterService
            preview = TuningAdapterService(root).prepare_operation("research", True, False, 0.2, 0.425)
            self.assertEqual(preview["field"], "baseCritChance")
            self.assertFalse(preview["mutation_performed"])

    def test_runtime_adapter_exposes_fail_closed_compatibility_matrix(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            from core.tuning_adapter import TuningAdapterService
            service = TuningAdapterService(root)
            compatible = service.compatibility_report(loader="EML", loader_api_version="1.3", game_build="1076226")
            incompatible = service.compatibility_report(loader="EML", loader_api_version="1.3", game_build="other")
            self.assertEqual(compatible["state"], "compatible")
            self.assertEqual(incompatible["state"], "incompatible")
            self.assertIn("shroudtopia", incompatible["future_adapters"])

    def test_runtime_adapter_captures_failure_and_recovery_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "adapters").mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (root / "adapters" / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            from core.tuning_adapter import TuningAdapterService
            service = TuningAdapterService(root)
            failure = service.capture_failure_session("EV-OP-FAIL", "Readback timed out", phase="verify", recovery_started=True)
            report = service.recovery_report("EV-OP-FAIL", "EV-BACKUP-1", readback_verified=False, rollback_verified=True, failure_session=str(failure))
            self.assertEqual(report["recovery_state"], "recovered")
            self.assertTrue(failure.is_file())

    def test_eml_tuning_adapter_readback_includes_verified_field_name(self):
        from core.tuning_adapter import TuningAdapterService
        result = TuningAdapterService.parse_runtime_readback(
            "[EMBERVAULT-EML-TUNING] context|loader=EML|api=1.3|build=1076226|operation=EV-OP-4\n"
            "[EMBERVAULT-EML-TUNING] write|field=baseCritChance|old=0.3|new=0.425|operation=EV-OP-4",
            "EV-OP-4",
        )
        self.assertEqual(result["field"], "baseCritChance")
        self.assertEqual(result["new_value"], 0.425)

    def test_research_records_operation_bound_runtime_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = EmbervaultRuntime.create(root)
            record = runtime.research.create("Adapter probe", "Readback is stable", "research")
            operation = runtime.operations.start(
                "research-evidence", profile_id="research", capability="research",
                capability_state="read-only", recovery_expectation="no live mutation")
            context = IntegrationContext.from_operation(
                operation, capability="research", capability_state="read-only",
                recovery_expectation="no live mutation")
            result = {"operation_id": operation.id, "field": "baseCritChance",
                      "loader": "EML", "readback_verified": True, "new_value": 0.425}
            updated = runtime.research.record_runtime_evidence(record.id, result, context)
            self.assertIn(operation.id, updated.evidence[0])
            self.assertIn('"profile_id": "research"', updated.evidence[0])

    def test_eml_tuning_adapter_readback_rejects_missing_or_mismatched_context(self):
        from core.tuning_adapter import TuningAdapterService
        write = "[EMBERVAULT-EML-TUNING] write|field=baseCritChance|old=0.3|new=0.425|operation=EV-OP-5"
        with self.assertRaises(ValueError):
            TuningAdapterService.parse_runtime_readback(write, "EV-OP-5")
        with self.assertRaises(ValueError):
            TuningAdapterService.parse_runtime_readback(
                "[EMBERVAULT-EML-TUNING] context|loader=EML|api=1.2|build=1076226|operation=EV-OP-5\n" + write,
                "EV-OP-5",
            )
        with self.assertRaises(ValueError):
            TuningAdapterService.parse_runtime_readback(
                "[EMBERVAULT-EML-TUNING] context|loader=EML|api=1.3|build=1076226|operation=EV-OP-6\n"
                "[EMBERVAULT-EML-TUNING] write|field=otherField|old=0.3|new=0.425|operation=EV-OP-6",
                "EV-OP-6",
            )

    def test_eml_tuning_adapter_rejects_operation_id_prefix_collisions(self):
        from core.tuning_adapter import TuningAdapterService
        with self.assertRaises(ValueError):
            TuningAdapterService.parse_runtime_readback(
                "[EMBERVAULT-EML-TUNING] context|loader=EML|api=1.3|build=1076226|operation=EV-OP-7X\n"
                "[EMBERVAULT-EML-TUNING] write|field=baseCritChance|old=0.3|new=0.425|operation=EV-OP-7X",
                "EV-OP-7",
            )

    def test_eml_tuning_adapter_write_gate_remains_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            from core.tuning_adapter import TuningAdapterService
            service = TuningAdapterService(root)
            preview = service.prepare_operation("research", True, False, 0.2, 0.425)
            with self.assertRaises(PermissionError):
                service.execute_operation(preview, profile_type="research", backup_verified=True, game_running=False)

    def test_eml_tuning_adapter_renders_scoped_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            from core.tuning_adapter import TuningAdapterService
            payload = TuningAdapterService(root).render_payload(0.2, "EV-OP-1")
            self.assertIn("operation=EV-OP-1", payload)
            self.assertIn("resource.data.baseCritChance = 0.2", payload)
            self.assertNotIn("enshrouded_local.json", payload)

    def test_eml_tuning_adapter_stages_owned_package_and_parses_readback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            from core.tuning_adapter import TuningAdapterService
            package = Path(__file__).parents[1] / "packages" / "eml-tuning-adapter"
            staged = TuningAdapterService(root).stage_package(package, root / "staging", 0.2, "EV-OP-2")
            self.assertIn("resource.data.baseCritChance = 0.2", (staged / "mod.lua").read_text())
            result = TuningAdapterService.parse_runtime_readback(
                "[EMBERVAULT-EML-TUNING] context|loader=EML|api=1.3|build=1076226|operation=EV-OP-2\n"
                "[EMBERVAULT-EML-TUNING] write|field=baseCritChance|old=0.425|new=0.2 operation=EV-OP-2",
                "EV-OP-2",
            )
            self.assertTrue(result["readback_verified"])

    def test_eml_tuning_adapter_stages_multiple_controlled_values_in_isolated_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            from core.tuning_adapter import TuningAdapterService
            service = TuningAdapterService(root)
            package = Path(__file__).parents[1] / "packages" / "eml-tuning-adapter"
            staged = [service.stage_package(package, root / "staging", value, f"EV-OP-VALUE-{index}")
                      for index, value in enumerate((0.0, 0.425, 1.0))]
            self.assertEqual(len({item.name for item in staged}), 3)
            self.assertIn("baseCritChance = 0", (staged[0] / "mod.lua").read_text())
            self.assertIn("baseCritChance = 0.425", (staged[1] / "mod.lua").read_text())
            self.assertIn("baseCritChance = 1", (staged[2] / "mod.lua").read_text())
            with self.assertRaises(ValueError):
                service.render_payload(-0.01, "EV-OP-INVALID")
            with self.assertRaises(ValueError):
                service.render_payload(1.01, "EV-OP-INVALID")

    def test_eml_tuning_adapter_verifies_expected_log_value(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            from core.tuning_adapter import TuningAdapterService
            log = root / "runtime.eml.log"
            log.write_text("[EMBERVAULT-EML-TUNING] context|loader=EML|api=1.3|build=1076226|operation=EV-OP-4\n"
                           "[EMBERVAULT-EML-TUNING] write|field=baseCritChance|old=0.425|new=0.2|operation=EV-OP-4\n", encoding="utf-8")
            result = TuningAdapterService(root).verify_log_file(log, "EV-OP-4", 0.2)
            self.assertEqual(result["status"], "verified")

    def test_eml_tuning_adapter_rejects_log_older_than_deployment(self):
        with tempfile.TemporaryDirectory() as temp:
            from core.tuning_adapter import TuningAdapterService
            log = Path(temp) / "runtime.eml.log"
            log.write_text(
                "[EMBERVAULT-EML-TUNING] context|loader=EML|api=1.3|build=1076226|operation=EV-OP-OLD\n"
                "[EMBERVAULT-EML-TUNING] write|field=baseCritChance|old=0.425|new=0.2|operation=EV-OP-OLD\n",
                encoding="utf-8",
            )
            import os
            os.utime(log, (100.0, 100.0))
            with self.assertRaises(ValueError):
                TuningAdapterService(Path(temp)).verify_log_file(log, "EV-OP-OLD", 0.2, minimum_mtime=200.0)

    def test_eml_tuning_adapter_rejects_symlinked_runtime_log(self):
        with tempfile.TemporaryDirectory() as temp:
            from core.tuning_adapter import TuningAdapterService
            target = Path(temp) / "real.eml.log"
            target.write_text("runtime", encoding="utf-8")
            link = Path(temp) / "linked.eml.log"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks are unavailable in this environment")
            with self.assertRaises(ValueError):
                TuningAdapterService(Path(temp)).verify_log_file(link, "EV-OP-LINK", 0.2)

    def test_eml_tuning_adapter_deploys_only_owned_staged_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter_dir = root / "adapters"
            adapter_dir.mkdir()
            source = Path(__file__).parents[1] / "adapters" / "eml-balancing-table.json"
            (adapter_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            from core.tuning_adapter import TuningAdapterService
            service = TuningAdapterService(root)
            package = Path(__file__).parents[1] / "packages" / "eml-tuning-adapter"
            staged = service.stage_package(package, root / "staging", 0.2, "EV-OP-3")
            game = root / "game"
            destination = service.deploy_staged_package(staged, game, game_running=False)
            self.assertTrue((destination / ".embervault-managed.json").exists())
            self.assertEqual(json.loads((destination / "mod.json").read_text())["entrypoint"], "mod.lua")
            service.undeploy_adapter(game)
            self.assertFalse(destination.exists())

    def test_eml_tuning_adapter_refuses_unowned_rollback(self):
        with tempfile.TemporaryDirectory() as temp:
            from core.tuning_adapter import TuningAdapterService
            game = Path(temp) / "game" / "mods" / "embervault.eml-tuning-adapter"
            game.mkdir(parents=True)
            (game / ".embervault-managed.json").write_text(json.dumps({"package_id": "other.mod", "managed_by": "other"}), encoding="utf-8")
            with self.assertRaises(PermissionError):
                TuningAdapterService(Path(temp)).undeploy_adapter(Path(temp) / "game")

    def test_catalog_sync_writes_repository_ready_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            destination = runtime.catalog.sync_to_directory(Path(temp) / "website" / "public")
            self.assertEqual(destination.name, "embervault-catalog.json")
            self.assertTrue(destination.is_file())
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["schema_version"], 1)

    def test_standalone_catalog_verifier_accepts_and_rejects_snapshots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = EmbervaultRuntime.create(root)
            catalog = runtime.catalog.export(root / "catalog.json")
            verifier = Path(__file__).resolve().parents[1] / "tools" / "verify_catalog.py"
            valid = subprocess.run([sys.executable, str(verifier), str(catalog)], capture_output=True, text=True)
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            payload = json.loads(catalog.read_text(encoding="utf-8"))
            payload["contract_versions"]["tuning_adapter"] = 0
            invalid = root / "invalid-catalog.json"
            invalid.write_text(json.dumps(payload), encoding="utf-8")
            rejected = subprocess.run([sys.executable, str(verifier), str(invalid)], capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)

    def test_sync_catalog_command_writes_validated_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tool = Path(__file__).resolve().parents[1] / "tools" / "sync_catalog.py"
            destination = root / "website"
            result = subprocess.run(
                [sys.executable, str(tool), str(destination), "--data-root", str(root / "runtime")],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((destination / "embervault-catalog.json").is_file())

    def test_catalog_validation_rejects_private_research_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            payload = runtime.catalog.build()
            payload["research"].append({"id": "private", "evidence": ["secret"]})
            with self.assertRaises(ValueError):
                runtime.catalog.validate(payload)

    def test_catalog_validation_rejects_unsanitized_knowledge_records(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            payload = runtime.catalog.build()
            payload["knowledge"].append({"id": "private", "content": "secret", "profile_id": "research"})
            with self.assertRaises(ValueError):
                runtime.catalog.validate(payload)

    def test_catalog_validation_requires_all_contract_versions(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            payload = runtime.catalog.build()
            del payload["contract_versions"]["content_project"]
            with self.assertRaisesRegex(ValueError, "content_project"):
                runtime.catalog.validate(payload)

    def test_catalog_validation_rejects_zero_contract_versions(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            payload = runtime.catalog.build()
            payload["contract_versions"]["research_record"] = 0
            with self.assertRaisesRegex(ValueError, "research_record"):
                runtime.catalog.validate(payload)

    def test_catalog_validation_rejects_identitiless_module_records(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            payload = runtime.catalog.build()
            payload["modules"].append({"name": "Missing identity"})
            with self.assertRaises(ValueError):
                runtime.catalog.validate(payload)

    def test_catalog_validation_rejects_invalid_module_process_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            payload = runtime.catalog.build()
            payload["modules"][0]["process_mode"] = "unknown"
            with self.assertRaises(ValueError):
                runtime.catalog.validate(payload)

    def test_catalog_export_orders_public_records_by_id(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            export = runtime.catalog.build()
            self.assertEqual([item["id"] for item in export["modules"]], sorted(item["id"] for item in export["modules"]))
            self.assertEqual([item["id"] for item in export["knowledge"]], sorted(item["id"] for item in export["knowledge"]))

    def test_knowledge_search_filters_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            self.assertEqual([item.id for item in runtime.knowledge.search("profiles")], ["profiles"])

    def test_troubleshooter_scan_is_read_only_and_repeatable(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            first = runtime.troubleshooter.scan()
            second = runtime.troubleshooter.scan()
            self.assertEqual(first, second)

    def test_module_catalog_exposes_capabilities(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            self.assertTrue(any("trainer" in item for item in runtime.modules.discover()["embervault.trainer"].capabilities))

    def test_backend_inspects_embedded_modules_with_operation_tracking(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend.inspectEmbeddedModules()
            self.assertIn("Inspected 1 embedded module", backend.lastSaveMessage)
            self.assertTrue(any(item.operation_type == "embedded-module-inspection"
                                and item.status == "succeeded"
                                for item in backend.operations.list_recent()))

    def test_package_options_show_package_type(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            self.assertTrue(any("mod" in item for item in backend.packageOptions))

    def test_backend_exposes_read_only_deployment_plan(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend.settings.game_path = temp
            self.assertTrue(any("enabled" in item.lower() or "ready" in item.lower()
                                for item in backend.deploymentOptions))
            backend.inspectDeploymentPlan()
            self.assertIn("Deployment plan", backend.lastSaveMessage)
            self.assertTrue(any("package-deployment-plan" in item for item in backend.recentOperations))

    def test_backend_exposes_external_mods_from_configured_game_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = EmbervaultRuntime.create(root)
            mods = root / "game" / "mods" / "outside"
            mods.mkdir(parents=True)
            (mods / "mod.json").write_text(json.dumps({
                "id": "outside.mod", "name": "Outside", "version": "1.0",
            }))
            backend = ControlCenterBackend(root, runtime=runtime)
            backend.settings.game_path = str(root / "game")
            self.assertTrue(any("Outside" in item for item in backend.externalPackageOptions))

    def test_backend_deploys_ready_packages_to_configured_game_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend.settings.game_path = temp
            self.assertFalse(backend.canDeploy)
            backend.inspectDeploymentPlan()
            self.assertTrue(backend.canDeploy)
            backend.deployReadyPackages()
            self.assertIn("Deployed 0 package", backend.lastSaveMessage)

    def test_backend_requires_current_deployment_plan_before_deploy(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend.settings.game_path = temp
            backend.deployReadyPackages()
            self.assertIn("Inspect the current deployment plan", backend.lastSaveMessage)
            self.assertFalse(backend.canDeploy)

    def test_backend_undeploy_refuses_unowned_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend.settings.game_path = temp
            backend.undeployPackage(0)
            self.assertIn("does not exist", backend.lastSaveMessage)

    def test_module_options_show_version_and_publisher(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            self.assertTrue(any("v0.1.0" in item and "EmberVault" in item and "embedded" in item for item in backend.moduleOptions))
            self.assertTrue(any("v0.1.0" in item and "EmberVault" in item and "separate" in item for item in backend.moduleOptions))

    def test_backend_guarded_research_launch_tracks_success(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend.selectProfile(1)
            backend.launchResearchWorker()
            self.assertIn("Completed guarded research worker", backend.lastSaveMessage)

    def test_backend_research_probe_persists_evidence_on_latest_record(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Probe", "Observe environment", "research")
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend.selectProfile(1)
            backend.launchResearchWorker()
            updated = next(item for item in runtime.research.list() if item.id == record.id)
            self.assertTrue(any(item.startswith("worker observation:") for item in updated.evidence))

    def test_backend_guarded_worker_receives_configured_game_path(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend.settings.game_path = "C:/Configured/Enshrouded"
            backend.selectProfile(1)
            backend.launchResearchWorker()
            self.assertIn("C:/Configured/Enshrouded", backend.lastSaveMessage)

    def test_backend_guarded_launch_reports_stable_profile_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend.launchResearchWorker()
            self.assertIn("Research profile", backend.lastSaveMessage)

    def test_backend_guarded_launch_terminates_timeout(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            process = Mock()
            process.communicate.side_effect = [subprocess.TimeoutExpired("worker", 15), ("", None)]
            backend.launcher = Mock()
            backend.launcher.launch.return_value = process
            backend.selectProfile(1)
            backend.launchResearchWorker()
            process.kill.assert_called_once_with()
            self.assertIn("timed out and was terminated", backend.lastSaveMessage)
            self.assertIn("Guarded module timed out", (Path(temp) / "logs" / "events.jsonl").read_text(encoding="utf-8"))

    def test_backend_rejects_invalid_worker_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            process = Mock(returncode=0)
            process.communicate.return_value = ('{"status":"ready"}', None)
            backend.launcher = Mock()
            backend.launcher.launch.return_value = process
            backend.selectProfile(1)
            backend.launchResearchWorker()
            self.assertIn("invalid", backend.lastSaveMessage.lower())

    def test_backend_rejects_worker_context_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            process = Mock(returncode=0)
            process.communicate.return_value = ('{"contract_version":1,"status":"ready","read_only":true,"profile":"wrong","operation":"wrong"}', None)
            backend.launcher = Mock()
            backend.launcher.launch.return_value = process
            backend.selectProfile(1)
            backend.launchResearchWorker()
            self.assertIn("invalid", backend.lastSaveMessage.lower())

    def test_backend_rejects_oversized_worker_output(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            process = Mock(returncode=0)
            process.communicate.return_value = ("x" * (1024 * 1024 + 1), None)
            backend.launcher = Mock()
            backend.launcher.launch.return_value = process
            backend.selectProfile(1)
            backend.launchResearchWorker()
            self.assertIn("too much output", backend.lastSaveMessage)

    def test_backend_rejects_worker_missing_schema_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            process = Mock(returncode=0)
            process.communicate.return_value = ('{"contract_version":1,"status":"ready","read_only":true,"profile":"research","operation":"x"}', None)
            backend.launcher = Mock()
            backend.launcher.launch.return_value = process
            backend.selectProfile(1)
            backend.launchResearchWorker()
            self.assertIn("invalid", backend.lastSaveMessage.lower())

    def test_backend_workspace_lists_are_profile_scoped(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            runtime.research.create("Stable note", "Stable hypothesis", "default")
            runtime.research.create("Research note", "Research hypothesis", "research")
            runtime.content.create("Stable project", "default", "Stable brief")
            runtime.content.create("Research project", "research", "Research brief")
            runtime.characters.create("Stable character", "default")
            runtime.characters.create("Research character", "research")
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            self.assertEqual(len(backend.researchOptions), 1)
            self.assertEqual(len(backend.contentOptions), 1)
            self.assertEqual(len(backend.characterOptions), 1)
            backend.selectProfile(1)
            self.assertIn("Research note", backend.researchOptions[0])
            self.assertIn("Research project", backend.contentOptions[0])
            self.assertIn("Research character", backend.characterOptions[0])

    def test_backend_profile_deletion_protects_owned_records(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = runtime.profiles.create_custom("Scratch")
            runtime.research.create("Owned", "Keep it", profile.id)
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend.selectProfile(2)
            backend.deleteActiveProfile()
            self.assertIn("owns project records", backend.lastSaveMessage)
            self.assertTrue(any(item.id == profile.id for item in backend.profile_service.list()))

    def test_backend_diagnostics_runs_and_audits_scan(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            backend = ControlCenterBackend(Path(temp), runtime=runtime)
            backend.runDiagnostics()
            self.assertIn("attention finding(s)", backend.lastSaveMessage)
            self.assertTrue(any(item.operation_type == "troubleshooter-scan" for item in runtime.operations.list_recent()))
            log_text = (Path(temp) / "logs" / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("Troubleshooter scan completed", log_text)

    def test_fallback_backend_can_delete_custom_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            backend = ControlCenterBackend(Path(temp))
            backend.profile_service.create_custom("Scratch")
            backend.profiles = backend.profile_service.list()
            backend.selectProfile(2)
            backend.deleteActiveProfile()
            self.assertIn("Deleted profile", backend.lastSaveMessage)

    def test_content_project_is_stored_outside_game_and_save_state(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            project = runtime.content.create("Ashen Furniture", "research", "A modular furniture experiment", "furniture", "Oak frame; modular corner joint")
            self.assertEqual(project.profile_id, "research")
            self.assertEqual(project.description, "A modular furniture experiment")
            self.assertEqual(project.design_type, "furniture")
            self.assertIn("Oak frame", project.design_notes)
            self.assertEqual(runtime.saves.list_backups(), [])

    def test_community_handoff_is_validated_and_conflicts_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            staged = runtime.community_sync.stage()
            payload = json.loads(staged.read_text(encoding="utf-8"))
            self.assertEqual(payload["authority"], "website")
            self.assertEqual(runtime.community_sync.compare(payload, payload)["status"], "identical")
            remote = json.loads(json.dumps(payload))
            remote["catalog"]["generated_at"] = "remote-version"
            result = runtime.community_sync.import_remote(remote)
            self.assertEqual(result["status"], "conflict")
            self.assertTrue(result["review_required"])
            self.assertFalse(result["automatic_overwrite"])

    def test_community_record_submission_is_versioned_and_conflict_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            path = runtime.community_sync.stage_record("knowledge", "EV-KNOW-1", 2,
                {"id": "EV-KNOW-1", "title": "Public note", "version": 2})
            local = json.loads(path.read_text(encoding="utf-8"))
            remote = json.loads(json.dumps(local))
            remote["record_version"] = 3
            remote["payload"]["title"] = "Remote note"
            result = runtime.community_sync.compare_record(local, remote)
            self.assertEqual(result["status"], "conflict")
            self.assertTrue(result["review_required"])

    def test_distribution_update_repair_and_uninstall_preserve_data(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            release = {"version": "1.1.0", "channel": "stable", "platform": "windows", "package_name": "embervault.exe"}
            self.assertTrue(runtime.distribution.check_update("1.0.0", release)["available"])
            (Path(temp) / "user-data.json").write_text("keep", encoding="utf-8")
            plan = runtime.distribution.uninstall_plan()
            self.assertTrue(plan["preserve_data"])
            self.assertIn("user-data.json", plan["preserved_paths"])
            repair = runtime.distribution.repair_plan([Path(temp) / "missing.dll"], {})
            self.assertTrue(repair["repair_required"])
            self.assertFalse(repair["automatic_repair"])

    def test_release_candidate_gate_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            audit = runtime.release.audit(["trainer"])
            self.assertFalse(audit["ready"])
            self.assertFalse(audit["unsupported_mutation_claimed"])
            with self.assertRaises(ValueError):
                runtime.release.create("1.0.0", ["trainer"])

    def test_research_collaboration_records_evidence_comparisons_and_report(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Collaboration probe", "The safe probe is reproducible", "research", "1076226", "1.0")
            runtime.research.add_attachment(record.id, "evidence/notes.txt", "observation", "Captured locally")
            runtime.research.add_reproduction_step(record.id, "Run the read-only probe")
            runtime.research.add_comparison(record.id, "baseline", "No mutation observed", "1076226")
            runtime.research.add_discussion_note(record.id, "Repeat with the next build")
            runtime.research.add_evidence(record.id, "Observed stable output")
            runtime.research.set_status(record.id, "completed")
            score = runtime.research.reproducibility_score(record.id)
            self.assertEqual(score["score"], 100)
            report = runtime.research.export_report(record.id)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["application_state"], "research-report")
            self.assertEqual(payload["report"]["attachment_count"], 1)
            self.assertNotIn(str(Path(temp)), report.read_text(encoding="utf-8"))

    def test_research_template_and_private_knowledge_promotion(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Compatibility finding", "Loader behavior is stable", "research",
                                             experiment_template="compatibility")
            runtime.research.add_evidence(record.id, "Observed stable behavior")
            runtime.research.set_status(record.id, "completed")
            entry = runtime.knowledge.create(record.title, "Research report", record.hypothesis,
                                              "Sanitized draft", related_ids=[record.id], evidence_refs=[record.id])
            runtime.research.link_context(record.id, knowledge=[entry.id])
            self.assertEqual(runtime.research.list()[-1].experiment_template, "compatibility")
            self.assertFalse(runtime.knowledge.entries()[-1].published)

    def test_character_and_trainer_expansion_remains_plan_only(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            character = runtime.characters.create("Ashen", "research")
            runtime.characters.update_plan(character.id, ["Tank"], ["Level armor"], ["Oak shield"], ["Guard"])
            runtime.characters.set_template(character.id, "tank")
            simulation = runtime.characters.simulate_progression(character.id, 20)
            self.assertEqual(simulation["application_state"], "plan-only")
            self.assertEqual(runtime.characters.list()[-1].version, 3)
            self.assertEqual(runtime.characters.list()[-1].build_template, "tank")

    def test_content_project_export_is_design_only(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            project = runtime.content.create("Ashen Furniture", "research", "A modular furniture experiment", "furniture", "Oak frame")
            destination = runtime.content.export(project)
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(payload["application_state"], "design-only")
            self.assertIn("published", payload["project"])
            self.assertIn("published_at", payload["project"])
            self.assertEqual(payload["project"]["id"], project.id)
            self.assertNotIn("game", destination.parts)

    def test_content_preview_is_structured_and_design_only(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            project = runtime.content.create("Ashen Furniture", "research", "A modular furniture experiment",
                                             "furniture", "Oak frame", ["assets/chair.png"], ["oak"],
                                             {"width": 2}, [], "Register ash_chair", "Build 1076226")
            runtime.content.link_references(project.id, ["EV-RES-1"], ["EV-KNOW-1"])
            runtime.content.record_design_decision(project.id, "Use oak joinery", "Research showed the joint survives the target load.", ["EV-RES-1"], ["EV-KNOW-1"])
            preview = runtime.content.preview(project.id)
            self.assertTrue(preview["ready_for_export"])
            self.assertEqual(preview["research_ids"], ["EV-RES-1"])
            self.assertEqual(preview["knowledge_ids"], ["EV-KNOW-1"])
            self.assertEqual(preview["application_state"], "design-only")
            self.assertFalse(preview["live_installation"])
            self.assertEqual(preview["design_decisions"][0]["decision"], "Use oak joinery")
            payload = json.loads(runtime.content.export(runtime.content.list()[-1]).read_text(encoding="utf-8"))
            self.assertEqual(payload["preview"]["project_id"], project.id)

    def test_content_project_tracks_structured_design_and_validates_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            project = runtime.content.create("Ashen Table", "research", "Furniture brief", "furniture", "Joinery notes", [],
                                            ["oak", "iron"], {"width": 2, "height": 1}, [], "Register ash_table", "Build 1076226")
            self.assertEqual(runtime.content.validate_design(project.id), [])
            self.assertEqual(runtime.content.set_status(project.id, "ready").status, "ready")
            exported = runtime.content.export(project)
            payload = json.loads(exported.read_text(encoding="utf-8"))
            self.assertEqual(payload["application_state"], "design-only")
            self.assertEqual(payload["project"]["materials"], ["oak", "iron"])
            self.assertEqual(payload["project"]["dimensions"]["width"], 2.0)
            self.assertNotIn("game_path", exported.read_text(encoding="utf-8"))

    def test_content_asset_references_are_relative_and_persisted(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            project = runtime.content.create("Furniture", "research", "Brief", "furniture", "Oak", ["assets/chair.png"])
            self.assertEqual(project.asset_references, ["assets/chair.png"])
            with self.assertRaises(ValueError):
                runtime.content.update_design(project.id, "furniture", "Oak", ["..\\outside.png"])

    def test_content_project_publication_is_explicit_and_catalog_sanitized(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            project = runtime.content.create("Furniture", "research", "A public design brief")
            self.assertEqual(runtime.catalog.build()["content_projects"], [])
            runtime.content.set_status(project.id, "ready")
            runtime.content.publish(project.id)
            public = runtime.catalog.build()["content_projects"]
            self.assertEqual(public[0]["id"], project.id)
            self.assertNotIn("description", public[0])
            runtime.content.unpublish(project.id)
            self.assertEqual(runtime.catalog.build()["content_projects"], [])

    def test_content_design_update_retracts_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            project = runtime.content.create("Furniture", "research", "A public design brief", "furniture", "Oak frame")
            runtime.content.set_status(project.id, "ready")
            runtime.content.publish(project.id)
            updated = runtime.content.update_design(project.id, "building", "Stone arch variation")
            self.assertEqual(updated.design_type, "building")
            self.assertFalse(updated.published)
            self.assertEqual(runtime.catalog.build()["content_projects"], [])

    def test_content_project_cannot_be_ready_without_brief(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            project = runtime.content.create("Unspecified", "research")
            with self.assertRaises(ValueError):
                runtime.content.set_status(project.id, "ready")

    def test_character_plan_export_is_save_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.characters.create("Ash", "research", "Build plan")
            destination = runtime.characters.export(record)
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(payload["application_state"], "plan-only")
            self.assertEqual(payload["character"]["id"], record.id)
            self.assertEqual(payload["application_state"], "plan-only")

    def test_character_plan_supports_structured_goals_and_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.characters.create("Ash", "research", "Build plan", ["Fire resistance"], ["Reach level 10"], ["Flame set"], ["Fireball"], "EV-BACKUP-VERIFIED")
            self.assertEqual(runtime.characters.validate_plan(record.id), [])
            updated = runtime.characters.update_plan(record.id, ["Fire resistance", "Mobility"], ["Reach level 10"], ["Flame set"], ["Fireball"], "EV-BACKUP-VERIFIED")
            self.assertEqual(updated.verified_backup_id, "EV-BACKUP-VERIFIED")
            self.assertEqual(updated.build_goals, ["Fire resistance", "Mobility"])

    def test_research_evidence_can_be_appended_to_record(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Test", "Observe", "research")
            updated = runtime.research.add_evidence(record.id, "Observed result")
            self.assertEqual(updated.evidence, ["Observed result"])

    def test_research_cannot_complete_without_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.research.create("Test", "Observe", "research")
            with self.assertRaises(ValueError):
                runtime.research.set_status(record.id, "completed")
            runtime.research.add_evidence(record.id, "Observed")
            self.assertEqual(runtime.research.set_status(record.id, "completed").status, "completed")

    def test_character_project_can_stage_valid_level(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.characters.create("Ash", "default")
            updated = runtime.characters.stage_level(record.id, 12)
            self.assertEqual(updated.planned_level, 12)

    def test_content_project_supports_guarded_status(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            project = runtime.content.create("Furniture", "research", "Test furniture brief")
            self.assertEqual(runtime.content.set_status(project.id, "ready").status, "ready")

    def test_character_project_is_separate_from_save_manager(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.characters.create("Ash", "default")
            self.assertEqual(record.profile_id, "default")
            self.assertEqual(runtime.saves.list_backups(), [])

    def test_character_level_rejects_boolean(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.characters.create("Ash", "default")
            with self.assertRaises(ValueError):
                runtime.characters.stage_level(record.id, True)

    def test_character_project_preserves_planning_notes(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.characters.create("Ash", "default", "Prioritize fire resistance")
            self.assertEqual(record.notes, "Prioritize fire resistance")

    def test_character_plan_notes_can_be_revised_without_save_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            record = runtime.characters.create("Ash", "default", "Initial plan")
            updated = runtime.characters.update_notes(record.id, "Revised progression plan")
            self.assertEqual(updated.notes, "Revised progression plan")
            self.assertEqual(runtime.saves.list_backups(), [])

    def test_trainer_plan_is_backup_bound_and_plan_only(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            profile = next(item for item in runtime.profiles.list() if item.id == "research")
            save_dir = Path(temp) / "save-source"
            save_dir.mkdir()
            (save_dir / "world.dat").write_text("safe", encoding="utf-8")
            backup = runtime.saves.backup(save_dir)
            plan = runtime.trainer.create(profile, "damage multiplier", "Read-only rehearsal", backup.id)
            destination = runtime.trainer.export(plan)
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(payload["application_state"], "trainer-plan-only")
            self.assertEqual(payload["plan"]["backup_id"], backup.id)

    def test_character_records_normalize_invalid_planned_level(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            runtime.characters.path.write_text(json.dumps([{
                "id": "EV-CHAR-BAD", "name": "Ash", "profile_id": "default", "planned_level": 999,
            }]))
            self.assertEqual(runtime.characters.list()[0].planned_level, 1)

    def test_character_records_skip_malformed_records(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            runtime.characters.path.write_text(json.dumps([
                {"id": "good", "name": "Ash", "profile_id": "default"},
                {"id": "bad", "profile_id": "default"},
            ]), encoding="utf-8")
            self.assertEqual([item.id for item in runtime.characters.list()], ["good"])

    def test_research_and_content_records_normalize_invalid_status(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            runtime.research.path.write_text(json.dumps([{
                "id": "EV-RES-BAD", "title": "Test", "hypothesis": "Test", "profile_id": "default",
                "status": "unknown", "evidence": "not-a-list",
            }]))
            runtime.content.path.write_text(json.dumps([{
                "id": "EV-CONTENT-BAD", "name": "Test", "profile_id": "default", "status": "unknown",
            }]))
            self.assertEqual(runtime.research.list()[0].status, "planned")
            self.assertEqual(runtime.research.list()[0].evidence, [])
            self.assertEqual(runtime.content.list()[0].status, "draft")

    def test_research_records_normalize_malformed_evidence_items(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            runtime.research.path.write_text(json.dumps([{
                "id": "EV-RES-EVIDENCE", "title": "Test", "hypothesis": "Test", "profile_id": "default",
                "status": "planned", "evidence": ["  observed  ", 12, "", "second"],
            }]))
            self.assertEqual(runtime.research.list()[0].evidence, ["observed", "second"])

    def test_research_and_content_skip_malformed_records(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            runtime.research.path.write_text(json.dumps([
                {"id": "good", "title": "Good", "hypothesis": "Test", "profile_id": "research"},
                {"id": "bad", "title": "Missing required fields"},
            ]), encoding="utf-8")
            runtime.content.path.write_text(json.dumps([
                {"id": "good", "name": "Good", "profile_id": "research"},
                {"id": "bad", "profile_id": "research"},
            ]), encoding="utf-8")
            self.assertEqual([item.id for item in runtime.research.list()], ["good"])
            self.assertEqual([item.id for item in runtime.content.list()], ["good"])

    def test_knowledge_skips_malformed_and_duplicate_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = EmbervaultRuntime.create(Path(temp))
            runtime.knowledge.path.write_text(json.dumps([
                {"id": "valid", "title": " Valid ", "category": "Guide", "summary": "Summary", "content": "Content"},
                {"id": "broken", "title": "Missing content", "category": "Guide"},
                {"id": "valid", "title": "Duplicate", "category": "Guide", "summary": "Other", "content": "Other"},
                "not-an-entry",
            ]), encoding="utf-8")
            entries = runtime.knowledge.entries()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].id, "valid")
            self.assertEqual(entries[0].title, "Valid")
            self.assertEqual(runtime.knowledge.path.parent.parent, Path(temp))


if __name__ == "__main__":
    unittest.main()
