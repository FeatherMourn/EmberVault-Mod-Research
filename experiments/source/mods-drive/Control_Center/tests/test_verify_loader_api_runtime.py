import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_loader_api_runtime import capture, validate_report


BUILD = "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"


class LoaderApiRuntimeEvidenceTests(unittest.TestCase):
    def test_capture_accepts_fresh_api_event_after_registry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            log = root / "latest.eml.log"
            loader = root / "dinput8.dll"
            loader.write_bytes(b"built loader")
            prefix = b'{"fields":{"message":"old unrelated event"}}\n'
            events = [
                {"level": "INFO", "fields": {"message": "Type registry loaded successfully", "version": BUILD}},
                {"level": "INFO", "fields": {"message": "Lua API initialized", "api_version": "1.1"}},
                {"level": "INFO", "fields": {"message": "Attaching runtime loader"}},
            ]
            log.write_bytes(prefix + b"\n".join(json.dumps(row).encode() for row in events) + b"\n")
            report = capture(log, len(prefix), BUILD, "1.1", loader)
            self.assertEqual(report["status"], "passed")
            self.assertFalse(report["mod_execution_observed"])
            self.assertEqual(validate_report(report, BUILD, "1.1"), [])

    def test_capture_rejects_stale_api_event_from_prior_session(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            log = root / "latest.eml.log"
            loader = root / "dinput8.dll"
            loader.write_bytes(b"built loader")
            events = [
                {"level": "INFO", "fields": {"message": "Type registry loaded successfully", "version": BUILD}},
                {"level": "INFO", "fields": {"message": "Lua API initialized", "api_version": "1.1"}},
                {"level": "INFO", "fields": {"message": "Type registry loaded successfully", "version": BUILD}},
                {"level": "INFO", "fields": {"message": "Attaching runtime loader"}},
            ]
            log.write_text("\n".join(json.dumps(row) for row in events) + "\n", encoding="utf-8")
            report = capture(log, 0, BUILD, "1.1", loader)
            self.assertEqual(report["status"], "failed")
            self.assertIn("API event is not proven after the current registry event", report["validation_errors"])

    def test_capture_rejects_current_session_errors(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            log = root / "latest.eml.log"
            loader = root / "dinput8.dll"
            loader.write_bytes(b"built loader")
            events = [
                {"level": "INFO", "fields": {"message": "Type registry loaded successfully", "version": BUILD}},
                {"level": "INFO", "fields": {"message": "Lua API initialized", "api_version": "1.1"}},
                {"level": "ERROR", "fields": {"message": "runtime initialization failed"}},
                {"level": "INFO", "fields": {"message": "Attaching runtime loader"}},
            ]
            log.write_text("\n".join(json.dumps(row) for row in events) + "\n", encoding="utf-8")
            report = capture(log, 0, BUILD, "1.1", loader)
            self.assertEqual(report["status"], "failed")
            self.assertIn("current session contains errors", report["validation_errors"])


if __name__ == "__main__":
    unittest.main()
