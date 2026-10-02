import json
import tempfile
import unittest
from pathlib import Path

from core.platform_services import GameBuildDetector, ModuleGraphService, RuntimeHealthService, feature_state


class PlatformServiceTests(unittest.TestCase):
    def test_build_detector_reads_explicit_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "build.json").write_text(json.dumps({"build_id": "1076226"}), encoding="utf-8")
            result = GameBuildDetector().detect(root)
            self.assertEqual(result.build_id, "1076226")
            self.assertEqual(result.confidence, "high")

    def test_build_detector_ignores_unrelated_cache_numbers_and_reads_eml_version(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / ".cache").mkdir(); (root / "logs").mkdir()
            (root / ".cache" / "files.json").write_text(json.dumps({"generated_at": "1790460093354"}), encoding="utf-8")
            (root / "logs" / "latest.eml.log").write_text(json.dumps({"fields": {
                "message": "Type registry loaded successfully",
                "version": "1076226|^/game38/branches/ea_update_08",
            }}) + "\n", encoding="utf-8")
            result = GameBuildDetector().detect(root)
            self.assertEqual(result.build_id, "1076226")
            self.assertEqual(result.confidence, "high")

    def test_runtime_health_is_conservative(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "logs"
            root.mkdir()
            (root / "latest.eml.log").write_text("REGISTERED|itemId=1\nUI_LINKS|matching_sets=1\n", encoding="utf-8")
            result = RuntimeHealthService().inspect(root.parent)
            self.assertEqual(result.status, "healthy")
            self.assertEqual(len(result.events), 2)

    def test_runtime_health_reports_loader_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "logs"
            root.mkdir()
            (root / "latest.eml.log").write_text("panic in mod loader\n", encoding="utf-8")
            self.assertEqual(RuntimeHealthService().inspect(root.parent).status, "failed")

    def test_runtime_health_honors_structured_error_level(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "logs"; root.mkdir()
            (root / "latest.eml.log").write_text(json.dumps({
                "level": "ERROR", "fields": {"message": "Error loading mod environment", "report": "missing mod.json"}
            }) + "\n", encoding="utf-8")
            result = RuntimeHealthService().inspect(root.parent)
            self.assertEqual(result.status, "failed")
            self.assertIn("missing mod.json", result.errors[0])

    def test_runtime_health_reports_recovery_after_earlier_error(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "logs"; root.mkdir()
            path = root / "latest.eml.log"
            path.write_text(json.dumps({"level": "ERROR", "fields": {"message": "old startup error"}}) + "\n" +
                            "REGISTERED|itemId=1\n", encoding="utf-8")
            result = RuntimeHealthService().inspect(root.parent)
            self.assertEqual(result.status, "degraded")
            self.assertEqual(len(result.errors), 1)

    def test_runtime_health_reads_reported_loader_api_version(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "logs"
            root.mkdir()
            event = {"fields": {"message": "Lua API initialized", "api_version": "1.1"}}
            (root / "latest.eml.log").write_text(json.dumps(event) + "\n", encoding="utf-8")
            result = RuntimeHealthService().inspect(root.parent)
            self.assertEqual(result.loader_api_version, "1.1")

    def test_runtime_health_ignores_unrecognized_loader_api_value(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "logs"
            root.mkdir()
            event = {"fields": {"message": "Lua API initialized", "api_version": "unknown"}}
            (root / "latest.eml.log").write_text(json.dumps(event) + "\n", encoding="utf-8")
            result = RuntimeHealthService().inspect(root.parent)
            self.assertIsNone(result.loader_api_version)

    def test_runtime_health_does_not_reuse_loader_api_from_older_session(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "logs"
            root.mkdir()
            old_api = {"fields": {"message": "Lua API initialized", "api_version": "1.1"}}
            new_session = {"fields": {"message": "Type registry loaded successfully", "version": "1076226"}}
            (root / "latest.eml.log").write_text(
                json.dumps(old_api) + "\n" + json.dumps(new_session) + "\n", encoding="utf-8")
            result = RuntimeHealthService().inspect(root.parent)
            self.assertIsNone(result.loader_api_version)

    def test_runtime_health_uses_current_registry_build_not_unrelated_log_numbers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "logs"
            root.mkdir()
            unrelated = {"fields": {"message": "cache generated 880650"}}
            registry = {"fields": {"message": "Type registry loaded successfully",
                                    "version": "1076226|^/game38/branches/ea_update_08"}}
            (root / "latest.eml.log").write_text(
                json.dumps(unrelated) + "\n" + json.dumps(registry) + "\n", encoding="utf-8")
            result = RuntimeHealthService().inspect(root.parent)
            self.assertEqual(result.build_id, "1076226")

    def test_runtime_health_ignores_errors_before_latest_registry_session(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "logs"; root.mkdir()
            path = root / "latest.eml.log"
            old = json.dumps({"level": "ERROR", "fields": {"message": "old mod directory error"}})
            session = json.dumps({"level": "INFO", "fields": {"message": "Type registry loaded successfully", "version": "1076226"}})
            path.write_text(old + "\n" + session + "\n" + "REGISTERED|itemId=1\n", encoding="utf-8")
            result = RuntimeHealthService().inspect(root.parent)
            self.assertEqual(result.status, "healthy")
            self.assertEqual(result.errors, ())

    def test_graph_orders_dependencies_and_reports_conflicts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"
            (root / "base").mkdir(parents=True)
            (root / "addon").mkdir()
            (root / "base" / "module.json").write_text(json.dumps({"id": "base", "dependencies": [], "load_order": 20}), encoding="utf-8")
            (root / "addon" / "module.json").write_text(json.dumps({"id": "addon", "dependencies": ["base"], "conflicts": ["other"], "load_order": 1}), encoding="utf-8")
            (root / "other").mkdir()
            (root / "other" / "module.json").write_text(json.dumps({"id": "other"}), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            self.assertLess(graph.order.index("base"), graph.order.index("addon"))
            self.assertTrue(any("Conflicts" in issue.message for issue in graph.issues))
            explanation = ModuleGraphService.explain(graph)
            addon = next(row for row in explanation if row["id"] == "addon")
            self.assertEqual(addon["dependencies"], ["base"])
            self.assertEqual(addon["feature_state"], "experimental")
            self.assertIsInstance(addon["load_index"], int)

    def test_feature_state_defaults_are_conservative(self):
        self.assertEqual(feature_state({"type": "kfc_resource_patch"}), "research-only")
        self.assertEqual(feature_state({"feature_state": "stable"}), "stable")
        self.assertEqual(feature_state({}), "experimental")

    def test_graph_strict_metadata_mode_rejects_legacy_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"; (root / "legacy").mkdir(parents=True)
            (root / "legacy" / "module.json").write_text(json.dumps({"id": "legacy"}), encoding="utf-8")
            compatible = ModuleGraphService(root).build()
            strict = ModuleGraphService(root).build(strict_metadata=True)
            self.assertFalse(any("valid feature_state" in issue.message for issue in compatible.issues))
            self.assertTrue(any("valid feature_state" in issue.message for issue in strict.issues))

    def test_graph_validates_dependency_versions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"
            (root / "base").mkdir(parents=True); (root / "addon").mkdir()
            (root / "base" / "module.json").write_text(json.dumps({"id": "base", "version": "1.2.0"}), encoding="utf-8")
            (root / "addon" / "module.json").write_text(json.dumps({"id": "addon", "dependencies": [{"id": "base", "version": ">=2.0.0"}]}), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            self.assertTrue(any("does not satisfy version" in issue.message for issue in graph.issues))

    def test_graph_reports_unconfirmed_module_loader_api_requirement(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"; (root / "addon").mkdir(parents=True)
            (root / "addon" / "module.json").write_text(json.dumps({
                "id": "addon", "required_loader_api_version": ">=1.2",
            }), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            self.assertTrue(any(issue.severity == "warning" and "Cannot confirm" in issue.message
                                for issue in graph.issues))

    def test_graph_does_not_assume_loader_api_without_runtime_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"; (root / "addon").mkdir(parents=True)
            (root / "addon" / "module.json").write_text(json.dumps({
                "id": "addon", "required_loader_api_version": ">=1.1",
            }), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            self.assertTrue(any(issue.severity == "warning" and "Cannot confirm" in issue.message
                                for issue in graph.issues))

    def test_graph_accepts_current_loader_api_requirement(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"; (root / "addon").mkdir(parents=True)
            (root / "addon" / "module.json").write_text(json.dumps({
                "id": "addon", "required_loader_api_version": ">=1.1",
            }), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            self.assertTrue(any(issue.severity == "warning" and "Cannot confirm" in issue.message
                                for issue in graph.issues))

    def test_named_loader_capability_remains_backward_compatible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"; (root / "addon").mkdir(parents=True)
            (root / "addon" / "module.json").write_text(json.dumps({
                "id": "addon", "required_loader_api": "assets.register_resource",
            }), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            self.assertFalse(graph.issues)

    def test_graph_rejects_unknown_dependency_version_constraints(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"
            (root / "base").mkdir(parents=True); (root / "addon").mkdir()
            (root / "base" / "module.json").write_text(json.dumps({"id": "base", "version": "1.0.0"}), encoding="utf-8")
            (root / "addon" / "module.json").write_text(json.dumps({"id": "addon", "dependencies": [{"id": "base", "version": "latest"}]}), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            self.assertTrue(any("Unsupported dependency version constraint" in issue.message for issue in graph.issues))

    def test_graph_reports_profile_module_that_is_not_installed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"
            root.mkdir(parents=True)
            graph = ModuleGraphService(root).build(enabled={"missing_module"})
            self.assertTrue(any(issue.module_id == "missing_module" and "not installed" in issue.message for issue in graph.issues))

    def test_graph_explanation_includes_dependency_versions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"
            (root / "base").mkdir(parents=True); (root / "addon").mkdir()
            (root / "base" / "module.json").write_text(json.dumps({"id": "base", "version": "1.2.0"}), encoding="utf-8")
            (root / "addon" / "module.json").write_text(json.dumps({"id": "addon", "dependencies": [{"id": "base", "version": ">=1.0.0"}]}), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            addon = next(row for row in ModuleGraphService.explain(graph) if row["id"] == "addon")
            self.assertEqual(addon["dependency_details"][0]["requested_version"], ">=1.0.0")
            self.assertEqual(addon["dependency_details"][0]["installed_version"], "1.2.0")

    def test_graph_rejects_duplicate_dependency_declarations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"
            (root / "base").mkdir(parents=True); (root / "addon").mkdir()
            (root / "base" / "module.json").write_text(json.dumps({"id": "base", "version": "1.0.0"}), encoding="utf-8")
            (root / "addon" / "module.json").write_text(json.dumps({"id": "addon", "dependencies": ["base", "base"]}), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            self.assertTrue(any("Duplicate dependency declaration" in issue.message for issue in graph.issues))

    def test_graph_rejects_self_dependency_and_duplicate_conflicts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"
            (root / "self").mkdir(parents=True)
            (root / "self" / "module.json").write_text(json.dumps({
                "id": "self", "dependencies": ["self"], "conflicts": ["self", "self"]
            }), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            self.assertTrue(any("depend on itself" in issue.message for issue in graph.issues))
            self.assertTrue(any("conflict with itself" in issue.message for issue in graph.issues))
            self.assertTrue(any("Duplicate conflict declaration" in issue.message for issue in graph.issues))

    def test_graph_rejects_non_array_dependency_and_conflict_fields(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"
            (root / "bad").mkdir(parents=True)
            (root / "bad" / "module.json").write_text(json.dumps({
                "id": "bad", "dependencies": "base", "conflicts": "other"
            }), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            self.assertTrue(any("Dependencies must be an array" in issue.message for issue in graph.issues))
            self.assertTrue(any("Conflicts must be an array" in issue.message for issue in graph.issues))

    def test_graph_rejects_blank_dependency_and_conflict_ids(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modules"
            (root / "bad").mkdir(parents=True)
            (root / "bad" / "module.json").write_text(json.dumps({
                "id": "bad", "dependencies": ["", {"id": None}], "conflicts": [" "]
            }), encoding="utf-8")
            graph = ModuleGraphService(root).build()
            self.assertTrue(any("Dependency ID cannot be empty" in issue.message for issue in graph.issues))
            self.assertTrue(any("Conflict ID cannot be empty" in issue.message for issue in graph.issues))



if __name__ == "__main__":
    unittest.main()
