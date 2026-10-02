import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.verify_live_loader import inspect
from tools.apply_smoke_profile import plan, restore_profile
from core.recovery import ModQuarantineService
from tools.verify_capability_audit import verify as verify_capability_audit


class VerifyLiveLoaderTests(unittest.TestCase):
    def test_versioned_isolated_content_profile_retains_stable_hub(self):
        profile_path = Path(__file__).parents[1] / "research" / "isolated_smoke_profile_20260927.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        self.assertEqual(profile["schema"], "control_center.smoke_profile.v1")
        self.assertEqual(profile["retain_modules"], ["enshrouded_mod_hub"])
        self.assertEqual(profile["exclude_modules"], ["flight_mod"])

    def test_reports_oversized_log_without_blocking_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dinput8.dll").write_bytes(b"proxy")
            (root / "mods").mkdir()
            (root / "logs").mkdir()
            research = root / "mods" / "research_probe"; research.mkdir()
            (research / "mod.json").write_text(json.dumps({"id": "research_probe", "feature_state": "research-only"}), encoding="utf-8")
            log = root / "logs" / "current.eml.log"
            with log.open("wb") as handle:
                handle.truncate(512 * 1024 * 1024)
            result = inspect(root)
            self.assertEqual(result["status"], "ready")
            self.assertTrue(result["warnings"])
            self.assertTrue(any("512 MiB" in warning for warning in result["warnings"]))
            self.assertEqual(result["research_only_mods"], ["research_probe"])
            self.assertEqual(result["classification_counts"]["research-only"], 1)
            self.assertTrue(any("research-only modules" in warning for warning in result["warnings"]))
            self.assertFalse(result["isolation_ready"])

    def test_reports_clean_small_log_without_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dinput8.dll").write_bytes(b"proxy")
            (root / "mods").mkdir()
            (root / "logs").mkdir()
            (root / "logs" / "current.eml.log").write_text(json.dumps({"ok": True}), encoding="utf-8")
            result = inspect(root)
            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["warnings"], [])

    def test_expected_build_is_checked_from_eml_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dinput8.dll").write_bytes(b"proxy")
            (root / "mods").mkdir()
            (root / "logs").mkdir()
            (root / "logs" / "current.eml.log").write_text(
                json.dumps({"version": "1076226|branch-test"}), encoding="utf-8")
            compatible = inspect(root, expected_build="1076226|branch-test")
            self.assertEqual(compatible["game_build"], "1076226|branch-test")
            self.assertEqual(compatible["build_compatibility"]["status"], "compatible")
            stale = inspect(root, expected_build="different-build")
            self.assertEqual(stale["build_compatibility"]["status"], "review_required")

    def test_numeric_expected_build_matches_full_eml_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dinput8.dll").write_bytes(b"proxy")
            (root / "mods").mkdir()
            (root / "logs").mkdir()
            full_version = "1076226|^/game38/branches/ea_update_08|timestamp"
            (root / "logs" / "current.eml.log").write_text(
                json.dumps({"version": full_version}), encoding="utf-8")
            result = inspect(root, expected_build="1076226")
            self.assertEqual(result["build_compatibility"]["status"], "compatible")
            self.assertEqual(result["build_compatibility"]["observed"], full_version)

    def test_research_only_can_be_explicitly_allowed_but_unclassified_cannot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dinput8.dll").write_bytes(b"proxy")
            (root / "mods").mkdir()
            (root / "mods" / "research_probe").mkdir()
            (root / "mods" / "research_probe" / "mod.json").write_text(
                json.dumps({"id": "research_probe", "feature_state": "research-only"}), encoding="utf-8")
            allowed = subprocess.run(
                [sys.executable, "tools/verify_live_loader.py", str(root), "--require-isolated", "--allow-research-only"],
                capture_output=True, text=True,
            )
            self.assertEqual(allowed.returncode, 0)
            (root / "mods" / "legacy").mkdir()
            (root / "mods" / "legacy" / "mod.json").write_text(json.dumps({"id": "legacy"}), encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, "tools/verify_live_loader.py", str(root), "--require-isolated", "--allow-research-only"],
                capture_output=True, text=True,
            )
            self.assertEqual(rejected.returncode, 2)

    def test_unclassified_modules_are_reported_for_manual_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dinput8.dll").write_bytes(b"proxy")
            (root / "mods" / "third_party").mkdir(parents=True)
            (root / "mods" / "third_party" / "mod.json").write_text(
                json.dumps({"id": "third_party", "name": "Third Party"}), encoding="utf-8")
            result = inspect(root)
            self.assertEqual(result["unclassified_mods"], ["third_party"])
            self.assertEqual(result["classification_counts"]["unclassified"], 1)
            self.assertEqual(result["unclassified_reasons"]["third_party"], "missing feature_state")
            self.assertTrue(any("without an explicit feature_state" in warning for warning in result["warnings"]))
            self.assertFalse(result["isolation_ready"])
            check = subprocess.run(
                [sys.executable, "tools/verify_live_loader.py", str(root), "--require-isolated"],
                capture_output=True, text=True, cwd=Path(__file__).parents[1])
            self.assertEqual(check.returncode, 2)

    def test_known_external_module_is_identified_without_being_isolated(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "mods" / "flight_mod").mkdir(parents=True); (root / "logs").mkdir(); (root / "dinput8.dll").write_bytes(b"")
            (root / "mods" / "flight_mod" / "mod.json").write_text(json.dumps({"id": "flight_mod", "name": "Flight Mod"}), encoding="utf-8")
            result = inspect(root)
            # The real repository allowlist is consulted by inspect; the
            # fixture uses the production module ID to exercise that policy.
            self.assertIn("flight_mod", result["external_third_party_mods"])
            self.assertFalse(result["isolation_ready"])

    def test_missing_manifest_is_unclassified_and_blocks_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dinput8.dll").write_bytes(b"proxy")
            (root / "mods" / "missing_manifest").mkdir(parents=True)
            result = inspect(root)
            self.assertEqual(result["unclassified_mods"], ["missing_manifest"])
            self.assertEqual(result["unclassified_reasons"]["missing_manifest"], "missing mod.json")
            check = subprocess.run(
                [sys.executable, "tools/verify_live_loader.py", str(root), "--require-isolated"],
                capture_output=True, text=True, cwd=Path(__file__).parents[1])
            self.assertEqual(check.returncode, 2)

    def test_research_only_manifest_flag_is_enforced_by_isolation_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dinput8.dll").write_bytes(b"proxy")
            (root / "mods" / "probe").mkdir(parents=True)
            (root / "mods" / "probe" / "mod.json").write_text(json.dumps({"id": "probe", "research_only": True}), encoding="utf-8")
            (root / "logs").mkdir()
            result = subprocess.run(
                [sys.executable, "tools/verify_live_loader.py", str(root), "--require-isolated"],
                capture_output=True, text=True, cwd=Path(__file__).parents[1])
            self.assertEqual(result.returncode, 2)

    def test_reports_stale_log_after_smoke_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dinput8.dll").write_bytes(b"proxy")
            (root / "mods").mkdir()
            (root / "logs").mkdir()
            log = root / "logs" / "current.eml.log"
            log.write_text("old", encoding="utf-8")
            baseline = log.stat().st_mtime + 10
            result = inspect(root, log_since=baseline)
            self.assertFalse(result["log_observability"]["fresh_session_observed"])
            self.assertTrue(any("no EML log" in warning for warning in result["warnings"]))

    def test_isolation_flag_is_available_for_automation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dinput8.dll").write_bytes(b"proxy")
            (root / "mods" / "research_probe").mkdir(parents=True)
            (root / "mods" / "research_probe" / "mod.json").write_text(
                json.dumps({"id": "research_probe", "feature_state": "research-only"}), encoding="utf-8")
            (root / "logs").mkdir()
            result = subprocess.run(
                [sys.executable, "tools/verify_live_loader.py", str(root), "--require-isolated"],
                capture_output=True, text=True, cwd=Path(__file__).parents[1])
            self.assertEqual(result.returncode, 2)

    def test_profile_validation_reports_inventory_difference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dinput8.dll").write_bytes(b"proxy")
            (root / "mods" / "one").mkdir(parents=True)
            (root / "mods" / "one" / "mod.json").write_text(json.dumps({"id": "one"}), encoding="utf-8")
            (root / "logs").mkdir()
            profile = root / "profile.json"
            profile.write_text(json.dumps({"id": "p", "exclude_modules": ["one", "missing"]}), encoding="utf-8")
            result = subprocess.run([sys.executable, "tools/verify_live_loader.py", str(root), "--profile", str(profile)], capture_output=True, text=True, cwd=Path(__file__).parents[1])
            self.assertEqual(result.returncode, 2)
            self.assertIn("missing", result.stdout)

    def test_smoke_profile_plan_accounts_for_live_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mods" / "one").mkdir(parents=True)
            (root / "mods" / "two").mkdir()
            (root / "mods" / "one" / "mod.json").write_text(json.dumps({"id": "one", "feature_state": "research-only"}), encoding="utf-8")
            (root / "logs").mkdir()
            (root / "logs" / "baseline.eml.log").write_text("baseline", encoding="utf-8")
            profile = root / "profile.json"
            profile.write_text(json.dumps({
                "schema": "control_center.smoke_profile.v1",
                "id": "test",
                "exclude_modules": ["one"],
                "retain_modules": ["two"],
            }), encoding="utf-8")
            result = plan(root, profile, root / "state")
            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["exclude"], ["one"])
            self.assertEqual(result["unaccounted_live_modules"], [])
            self.assertEqual(result["research_only_exclusions"], ["one"])
            self.assertEqual(result["log_baseline"]["path"].split("\\")[-1], "baseline.eml.log")

    def test_smoke_profile_restore_works_after_modules_are_quarantined(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mods = root / "mods"; mods.mkdir()
            module = mods / "one"; module.mkdir()
            (module / "mod.json").write_text(json.dumps({"id": "one"}), encoding="utf-8")
            service = ModQuarantineService(root / "state")
            service.quarantine(mods, "one", "isolated smoke profile unrelated")
            self.assertFalse(module.exists())
            restored = restore_profile(root / "state", "test")
            self.assertEqual(restored, [])
            # The profile label is exact, so unrelated recovery records are not adopted.
            # Rename the record's reason through the public record file to model the target profile.
            record = next(iter(service.records()))
            data = json.loads(record.record_path.read_text(encoding="utf-8"))
            data["reason"] = "isolated smoke profile target"
            record.record_path.write_text(json.dumps(data), encoding="utf-8")
            restored = restore_profile(root / "state", "target")
            self.assertEqual(len(restored), 1)
            self.assertTrue(module.is_dir())

    def test_capability_audit_verifier_checks_phase_coverage_and_evidence(self):
        audit = Path(__file__).parents[1] / "research" / "CAPABILITY_AUDIT_20260927.json"
        result = verify_capability_audit(audit)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["phases"], [1, 2, 3, 4, 5, 6])


if __name__ == "__main__":
    unittest.main()
