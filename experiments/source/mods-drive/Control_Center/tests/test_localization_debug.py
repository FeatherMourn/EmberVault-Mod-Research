import json
import tempfile
import unittest
from pathlib import Path

from core.localization_debug import LocalizationDebugger


class LocalizationDebuggerTests(unittest.TestCase):
    def test_reports_registration_and_missing_keys(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "latest.eml.log"
            lines = [
                {"fields": {"message": "Type registry loaded successfully", "version": "1076226|kfc"}},
                {"fields": {"message": "[CC-LOCALIZATION] REGISTER|ok=true"}},
                {"fields": {"message": "[CC-LOCALIZATION] KEY|known_key|locale=En_Us"}},
            ]
            log.write_text("\n".join(json.dumps(line) for line in lines), encoding="utf-8")
            result = LocalizationDebugger().inspect(log, ["known_key", "missing_key"])
            self.assertEqual(result.build_id, "1076226")
            self.assertEqual(result.status, "review_required")
            self.assertEqual(result.missing_keys, ("missing_key",))
            self.assertFalse(result.ui_consumption_verified)

    def test_successful_registration_without_expected_keys_is_runtime_verified(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "latest.eml.log"
            log.write_text(json.dumps({"fields": {"message": "[CC-LOCALIZATION] REGISTER|ok=true"}}), encoding="utf-8")
            result = LocalizationDebugger().inspect(log)
            self.assertEqual(result.status, "runtime_registration_verified")

    def test_reports_last_marker_and_safe_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "latest.eml.log"
            log.write_text("\n".join([
                json.dumps({"fields": {"message": "[CC-LOCALIZATION] TAG|ok=true|result=tag"}}),
                json.dumps({"fields": {"message": "[CC-LOCALIZATION] COLLECTION|skipped=safe_default_requires_explicit_opt_in"}}),
            ]), encoding="utf-8")
            result = LocalizationDebugger().inspect(log)
            self.assertEqual(result.last_marker, "COLLECTION")
            self.assertEqual(result.boundary, "collection")
            self.assertFalse(result.panic_observed)

    def test_flags_loader_panic_as_unsafe_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "latest.eml.log"
            log.write_text(json.dumps({"fields": {"message": "panic in a function that cannot unwind"}}), encoding="utf-8")
            result = LocalizationDebugger().inspect(log)
            self.assertTrue(result.panic_observed)
            self.assertIn("Do not repeat", result.next_safe_action)

    def test_validates_persisted_boundary_report(self):
        report = {
            "schema": "control_center.localization_boundary_report.v1",
            "status": "review_required", "boundary": "no_marker", "last_marker": "",
            "panic_observed": False, "registration": False, "missing_keys": [], "issues": [],
            "next_safe_action": "keep research-only", "log_sha256": "a" * 64,
        }
        self.assertEqual(LocalizationDebugger.validate_report(report), ())
        report["panic_observed"] = "false"
        self.assertTrue(LocalizationDebugger.validate_report(report))

    def test_session_offset_excludes_prior_markers(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "latest.eml.log"
            prefix = json.dumps({"fields": {"message": "[CC-LOCALIZATION] REGISTER|ok=true"}}) + "\n"
            suffix = json.dumps({"fields": {"message": "[CC-LOCALIZATION] TAG|ok=true"}}) + "\n"
            log.write_text(prefix + suffix, encoding="utf-8")
            result = LocalizationDebugger().inspect(log, from_byte=len(prefix.encode("utf-8")))
            self.assertEqual(result.last_marker, "TAG")
            self.assertFalse(result.status == "runtime_registration_verified")


if __name__ == "__main__":
    unittest.main()
