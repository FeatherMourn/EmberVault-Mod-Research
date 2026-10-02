import unittest
import json
from pathlib import Path


class PackagingContractTests(unittest.TestCase):
    def test_release_assets_exist(self):
        root = Path(__file__).resolve().parents[1]
        for relative in (
            "ui/Main.qml",
            "contracts/module-manifest.schema.json",
            "contracts/package-manifest.schema.json",
            "contracts/catalog.schema.json",
            "contracts/worker-result.schema.json",
            "contracts/game-settings.schema.json",
            "contracts/tuning-adapter.schema.json",
            "contracts/character-plan.schema.json",
            "contracts/content-project.schema.json",
            "knowledge/entries.json",
            "modules/example/module.json",
            "modules/example/module.py",
            "modules/trainer/module.json",
            "modules/trainer/trainer_stub.py",
            "modules/research/module.json",
            "modules/research/research_stub.py",
            "modules/content-creator/module.json",
            "modules/content-creator/content_stub.py",
            "contracts/knowledge-entry.schema.json",
            "contracts/research-summary.schema.json",
            "contracts/trainer-plan.schema.json",
            "contracts/integration-context.schema.json",
            "contracts/promotion-evidence.schema.json",
            "modules/tuning-audit/module.json",
            "modules/tuning-audit/tuning_stub.py",
            "packages/example-mod/package.json",
            "adapters/eml-balancing-table.json",
            "packages/eml-tuning-adapter/package.json",
            "packages/eml-tuning-adapter/mod.json",
            "packages/eml-tuning-adapter/mod.lua",
            "templates/module/module.json",
            "templates/module/module.py",
            "templates/module/README.md",
            "tools/verify_release.py",
            "tools/verify_catalog.py",
            "tools/sync_catalog.py",
        ):
            self.assertTrue((root / relative).is_file(), relative)

    def test_data_file_layout_matches_setuptools_wheel_convention(self):
        root = Path(__file__).resolve().parents[1]
        metadata = (root / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"ui" = ["ui/Main.qml"]', metadata)
        self.assertIn('dependencies = ["PySide6>=6.8"]', metadata)

    def test_seed_assets_have_installed_prefix_fallbacks(self):
        root = Path(__file__).resolve().parents[1]
        for relative in ("core/knowledge.py", "core/modules.py", "core/packages.py"):
            text = (root / relative).read_text(encoding="utf-8")
            self.assertIn("sys.prefix", text)

    def test_contracts_declare_strict_manifest_entries(self):
        root = Path(__file__).resolve().parents[1]
        module_schema = (root / "contracts/module-manifest.schema.json").read_text(encoding="utf-8")
        package_schema = (root / "contracts/package-manifest.schema.json").read_text(encoding="utf-8")
        self.assertIn('"uniqueItems": true', module_schema)
        self.assertIn('"minLength": 1', module_schema)
        self.assertIn('"minLength": 1', package_schema)

    def test_contract_documents_are_valid_json(self):
        root = Path(__file__).resolve().parents[1]
        for path in (root / "contracts").glob("*.json"):
            with self.subTest(path=path.name):
                self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")), dict)

    def test_release_verifier_lists_trainer_contract(self):
        root = Path(__file__).resolve().parents[1]
        verifier = (root / "tools" / "verify_release.py").read_text(encoding="utf-8")
        self.assertIn('"contracts/trainer-plan.schema.json"', verifier)

    def test_release_verifier_lists_tuning_adapter_contract(self):
        root = Path(__file__).resolve().parents[1]
        verifier = (root / "tools" / "verify_release.py").read_text(encoding="utf-8")
        self.assertIn('"contracts/tuning-adapter.schema.json"', verifier)

    def test_release_verifier_validates_packaged_json_content(self):
        root = Path(__file__).resolve().parents[1]
        verifier = (root / "tools" / "verify_release.py").read_text(encoding="utf-8")
        self.assertIn("json.loads", verifier)
        self.assertIn('"knowledge/entries.json"', verifier)
        self.assertIn("Packaged knowledge catalog must contain at least one entry", verifier)

    def test_catalog_verifier_enforces_module_process_mode(self):
        root = Path(__file__).resolve().parents[1]
        verifier = (root / "tools" / "verify_catalog.py").read_text(encoding="utf-8")
        self.assertIn("process_mode", verifier)
        self.assertIn('"embedded", "separate"', verifier)

    def test_catalog_schema_declares_tuning_adapter_records(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "contracts/catalog.schema.json").read_text(encoding="utf-8"))
        self.assertIn("tuning_adapters", schema["required"])
        self.assertIn("tuning_adapters", schema["properties"])
        self.assertFalse(schema["properties"]["contract_versions"]["additionalProperties"])

    def test_tuning_adapter_contract_declares_safety_boundaries(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "contracts/tuning-adapter.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        for field in ("process_mode", "supported_setting_keys", "backup_requirements", "mutation_scope", "verification_steps"):
            self.assertIn(field, schema["required"])
        self.assertEqual(schema["properties"]["process_mode"]["enum"], ["embedded", "separate"])
        self.assertTrue(schema["additionalProperties"] is False)

    def test_catalog_verifier_uses_core_contract_validation(self):
        root = Path(__file__).resolve().parents[1]
        verifier = (root / "tools" / "verify_catalog.py").read_text(encoding="utf-8")
        self.assertIn("def validate_catalog", verifier)

    def test_windows_ci_smoke_tests_installed_wheel(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        windows_section = workflow.split("  windows:", 1)[1]
        self.assertIn("Build wheel", windows_section)
        self.assertIn("Verify release assets", windows_section)
        self.assertIn("Smoke-test installed wheel", windows_section)
        self.assertIn("shell: pwsh", windows_section)
        self.assertIn("control_center.app --smoke-test", windows_section)

    def test_ci_verifies_catalog_handoff(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("Verify catalog handoff", workflow)
        self.assertIn("tools/sync_catalog.py", workflow)
        self.assertIn("tools/verify_catalog.py", workflow)

    def test_terminology_contract_freezes_public_vocabulary(self):
        root = Path(__file__).resolve().parents[1]
        terminology = (root / "docs" / "TERMINOLOGY.md").read_text(encoding="utf-8")
        for term in ("EmberVault Control Center", "EmberVault Core", "Profile", "Package", "Module", "Staged-only"):
            self.assertIn(term, terminology)

    def test_module_boundary_contract_declares_guarded_capabilities(self):
        root = Path(__file__).resolve().parents[1]
        boundaries = (root / "docs" / "MODULE_BOUNDARIES.md").read_text(encoding="utf-8")
        for capability in ("`research`", "`trainer`", "`content-creator`", "`tuning-audit`"):
            self.assertIn(capability, boundaries)
        self.assertIn("Promotion rule", boundaries)

    def test_module_template_contains_contract_safety_and_recovery_fields(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "templates/module/module.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["contract_version"], 1)
        self.assertIn("safety", manifest)
        self.assertIn("recovery", manifest)
        self.assertTrue((root / "templates/module/module.py").is_file())
        self.assertTrue((root / "templates/module/README.md").is_file())
        from core.modules import ModuleManifest
        parsed = ModuleManifest.from_file(root / "templates/module/module.json")
        self.assertEqual(parsed.contract_version, 1)
        self.assertTrue(parsed.safety["read_only"])
        self.assertIn("replace-me.inspect", parsed.operation_types)


if __name__ == "__main__":
    unittest.main()
