import json
import os
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class InstallResearchProbeTests(unittest.TestCase):
    def test_guide_documents_beginner_install_alias(self):
        guide = (Path(__file__).parents[1] / "docs" / "RESEARCH_PROBE_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("--install --allow-research", guide)

    def test_missing_entrypoint_is_rejected_before_install(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); probe = root / "probe"; game = root / "game"
            probe.mkdir(); (game / "mods").mkdir(parents=True)
            (probe / "mod.json").write_text(json.dumps({
                "id": "incomplete", "name": "Incomplete", "version": "0.1.0",
                "author": "Test", "loader": "EML", "feature_state": "research-only",
                "entrypoint": "src/mod.lua",
            }), encoding="utf-8")
            result = subprocess.run([sys.executable, "tools/install_research_probe.py", str(probe), str(game), "--storage", str(root / "storage")], cwd=Path(__file__).parents[1], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("entrypoint is missing", result.stderr)

    def test_known_stalling_resource_families_are_explicitly_guarded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); probe = root / "probe"; game = root / "game"
            (probe / "src").mkdir(parents=True); (game / "mods").mkdir(parents=True)
            (probe / "mod.json").write_text(json.dumps({"id": "probe", "name": "Probe", "version": "0.1.0", "author": "Test", "loader": "EML", "feature_state": "research-only", "entrypoint": "src/mod.lua"}), encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("local t = 'keen::AnimationGraphResource2_0'", encoding="utf-8")
            result = subprocess.run([sys.executable, "tools/install_research_probe.py", str(probe), str(game), "--storage", str(root / "storage")], cwd=Path(__file__).parents[1], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("known-stalling resource families", result.stderr)

    def test_ecs_interaction_schema_is_guarded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); probe = root / "probe"; game = root / "game"
            (probe / "src").mkdir(parents=True); (game / "mods").mkdir(parents=True)
            (probe / "mod.json").write_text(json.dumps({"id": "probe", "name": "Probe", "version": "0.1.0", "author": "Test", "loader": "EML", "feature_state": "research-only", "entrypoint": "src/mod.lua"}), encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("local t = 'keen::ecs::InteractionOffer'", encoding="utf-8")
            result = subprocess.run([sys.executable, "tools/install_research_probe.py", str(probe), str(game), "--storage", str(root / "storage")], cwd=Path(__file__).parents[1], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("known-stalling resource families", result.stderr)

    def test_metadata_only_enumeration_allows_stalling_payload_family(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); probe = root / "probe"; game = root / "game"
            (probe / "src").mkdir(parents=True); (game / "mods").mkdir(parents=True)
            (probe / "mod.json").write_text(json.dumps({"id": "probe", "name": "Probe", "version": "0.1.0", "author": "Test", "loader": "EML", "feature_state": "research-only", "entrypoint": "src/mod.lua"}), encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("return game.assets.get_resource_metadata_by_type('keen::AnimationGraphResource2_0')", encoding="utf-8")
            result = subprocess.run([sys.executable, "tools/install_research_probe.py", str(probe), str(game), "--storage", str(root / "storage")], cwd=Path(__file__).parents[1], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["mode"], "dry_run")

    def test_template_resource_metadata_is_blocked_after_runtime_stall(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); probe = root / "probe"; game = root / "game"
            (probe / "src").mkdir(parents=True); (game / "mods").mkdir(parents=True)
            (probe / "mod.json").write_text(json.dumps({"id": "probe", "name": "Probe", "version": "0.1.0", "author": "Test", "loader": "EML", "feature_state": "research-only", "entrypoint": "src/mod.lua"}), encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("return game.assets.get_resource_metadata_by_type('keen::TemplateResource')", encoding="utf-8")
            result = subprocess.run([sys.executable, "tools/install_research_probe.py", str(probe), str(game), "--storage", str(root / "storage")], cwd=Path(__file__).parents[1], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("TemplateResource is quarantined", result.stderr)

    def test_template_resource_requires_explicit_boundary_override(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); probe = root / "probe"; game = root / "game"
            (probe / "src").mkdir(parents=True); (game / "mods").mkdir(parents=True)
            (probe / "mod.json").write_text(json.dumps({"id": "probe", "name": "Probe", "version": "0.1.0", "author": "Test", "loader": "EML", "feature_state": "research-only", "entrypoint": "src/mod.lua"}), encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("return game.assets.get_resource_metadata_by_type('keen::TemplateResource')", encoding="utf-8")
            result = subprocess.run([sys.executable, "tools/install_research_probe.py", str(probe), str(game), "--storage", str(root / "storage"), "--allow-unsafe-boundary"], cwd=Path(__file__).parents[1], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["mode"], "dry_run")

    def test_invalid_eml_capability_is_rejected_before_install(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); probe = root / "probe"; game = root / "game"
            (probe / "src").mkdir(parents=True); (game / "mods").mkdir(parents=True)
            (probe / "mod.json").write_text(json.dumps({"id": "probe", "name": "Probe", "version": "0.1.0", "author": "Test", "loader": "EML", "feature_state": "research-only", "capabilities": ["research.read-only"], "entrypoint": "src/mod.lua"}), encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            result = subprocess.run([sys.executable, "tools/install_research_probe.py", str(probe), str(game), "--storage", str(root / "storage")], cwd=Path(__file__).parents[1], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unsupported EML capability", result.stderr)

    def test_default_mode_is_dry_run_and_does_not_copy_probe(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); probe = root / "probe"; game = root / "game"; (probe / "src").mkdir(parents=True); (game / "mods").mkdir(parents=True); (game / "logs").mkdir(); (game / "dinput8.dll").write_bytes(b"fixture")
            (probe / "mod.json").write_text(json.dumps({"id": "probe", "name": "Probe", "version": "0.1.0", "author": "Test", "loader": "EML", "feature_state": "research-only", "entrypoint": "src/mod.lua"}), encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            (game / "logs" / "session.eml.log").write_text('"version": "test-build"', encoding="utf-8")
            digest = hashlib.sha256()
            for file in sorted(path for path in probe.rglob("*") if path.is_file()):
                digest.update(file.relative_to(probe).as_posix().encode())
                digest.update(file.read_bytes())
            cycle = root / "RESEARCH_CYCLE.json"
            cycle.write_text(json.dumps({"staged_probe_sha256": digest.hexdigest()}), encoding="utf-8")
            report_path = root / "report.json"
            result = subprocess.run([sys.executable, "tools/install_research_probe.py", str(probe), str(game), "--storage", str(root / "storage"), "--expected-build", "test-build", "--cycle", str(cycle), "--output", str(report_path)], cwd=Path(__file__).parents[1], capture_output=True, text=True, check=True)
            report = json.loads(result.stdout)
            self.assertEqual(report["mode"], "dry_run")
            self.assertEqual(report["build_compatibility"]["observed"], "test-build")
            self.assertEqual(report["build_compatibility"]["status"], "compatible")
            self.assertTrue(report["research_cycle_binding"]["probe_sha256"])
            self.assertEqual(report["session_baseline"]["path"], str(game / "logs" / "session.eml.log"))
            self.assertEqual(report["session_baseline"]["size"], (game / "logs" / "session.eml.log").stat().st_size)
            self.assertFalse((game / "mods" / "probe").exists())
            self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["mode"], "dry_run")

    def test_apply_requires_explicit_research_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); probe = root / "probe"; game = root / "game"; (probe / "src").mkdir(parents=True); (game / "mods").mkdir(parents=True)
            (probe / "mod.json").write_text(json.dumps({"id": "probe", "name": "Probe", "version": "0.1.0", "author": "Test", "loader": "EML", "feature_state": "research-only", "entrypoint": "src/mod.lua"}), encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            result = subprocess.run([sys.executable, "tools/install_research_probe.py", str(probe), str(game), "--storage", str(root / "storage"), "--apply"], cwd=Path(__file__).parents[1], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("--allow-research", result.stderr)

    def test_expected_build_mismatch_blocks_operation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); probe = root / "probe"; game = root / "game"; (probe / "src").mkdir(parents=True); (game / "mods").mkdir(parents=True); (game / "logs").mkdir()
            (probe / "mod.json").write_text(json.dumps({"id": "probe", "name": "Probe", "version": "0.1.0", "author": "Test", "loader": "EML", "feature_state": "research-only", "entrypoint": "src/mod.lua"}), encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            (game / "logs" / "session.eml.log").write_text('"version": "old-build"', encoding="utf-8")
            result = subprocess.run([sys.executable, "tools/install_research_probe.py", str(probe), str(game), "--storage", str(root / "storage"), "--expected-build", "new-build"], cwd=Path(__file__).parents[1], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("build mismatch", result.stderr)

    def test_remove_uses_ownership_record(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); probe = root / "probe"; game = root / "game"
            (probe / "src").mkdir(parents=True); (game / "mods").mkdir(parents=True); (game / "logs").mkdir()
            (probe / "mod.json").write_text(json.dumps({"id":"probe","name":"Probe","version":"0.1.0","author":"Test","loader":"EML","feature_state":"research-only","capabilities":["patch"],"entrypoint":"src/mod.lua"}), encoding="utf-8")
            (probe / "src" / "mod.lua").write_text("return {}", encoding="utf-8")
            args = [sys.executable, "tools/install_research_probe.py", str(probe), str(game), "--storage", str(root / "storage"), "--allow-research"]
            test_env = os.environ.copy(); test_env["CONTROL_CENTER_TEST_ALLOW_RUNNING_GAME"] = "1"
            applied = subprocess.run(args + ["--install"], cwd=Path(__file__).parents[1], env=test_env, capture_output=True, text=True)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            removed = subprocess.run(args + ["--remove"], cwd=Path(__file__).parents[1], env=test_env, capture_output=True, text=True)
            self.assertEqual(removed.returncode, 0, removed.stderr)
            self.assertTrue(json.loads(removed.stdout)["removed"])
            self.assertFalse((game / "mods" / "probe").exists())


if __name__ == "__main__":
    unittest.main()
