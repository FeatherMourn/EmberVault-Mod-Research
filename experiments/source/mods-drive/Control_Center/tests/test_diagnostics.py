import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from core.diagnostics import DiagnosticService, SupportBundleService


class DiagnosticsTests(unittest.TestCase):
    def test_parse_and_search_structured_events(self):
        with tempfile.TemporaryDirectory() as td:
            logs = Path(td) / "logs"; logs.mkdir()
            path = logs / "latest.eml.log"
            path.write_text("REGISTERED|itemId=1\n[WARN] compatibility uncertain\npanic in module\n", encoding="utf-8")
            service = DiagnosticService()
            self.assertEqual(len(service.search(logs, "registered")), 1)
            self.assertEqual(len(service.search(logs, level="error")), 1)
            summary = service.summarize(logs)
            self.assertEqual(summary["status"], "failed")
            self.assertEqual(summary["latest_status"], "failed")
            self.assertEqual(summary["historical_errors"], 0)

    def test_support_bundle_is_bounded_and_contains_summary(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "control"; (base / "profiles").mkdir(parents=True); (base / "modules" / "sample").mkdir(parents=True)
            (base / "profiles" / "active_profile.json").write_text("{}", encoding="utf-8")
            (base / "modules" / "sample" / "module.json").write_text(json.dumps({"id": "sample"}), encoding="utf-8")
            (base / "research").mkdir()
            (base / "research" / "content_catalog.json").write_text("{}", encoding="utf-8")
            (base / "research" / "BUILDER_PLACEMENT_FEASIBILITY_20260927.md").write_text("builder evidence", encoding="utf-8")
            (base / "research" / "localization_boundary_reports").mkdir()
            (base / "research" / "localization_boundary_reports" / "boundary.json").write_text("{}", encoding="utf-8")
            (base / "research" / "feasibility_reports").mkdir()
            (base / "research" / "feasibility_reports" / "builder.json").write_text("{}", encoding="utf-8")
            (base / "research" / "live_preflight_stable.json").write_text("{}", encoding="utf-8")
            game = Path(td) / "game"; (game / "logs").mkdir(parents=True); (game / "logs" / "one.eml.log").write_text("ok", encoding="utf-8")
            archive = SupportBundleService().create(base, game, Path(td) / "support.zip")
            with zipfile.ZipFile(archive) as z:
                self.assertIn("summary.json", z.namelist())
                self.assertIn("health.json", z.namelist())
                self.assertIn("profiles/active_profile.json", z.namelist())
                self.assertIn("research/content_catalog.json", z.namelist())
                self.assertIn("research/BUILDER_PLACEMENT_FEASIBILITY_20260927.md", z.namelist())
                self.assertIn("research/localization_boundary_reports/boundary.json", z.namelist())
                self.assertIn("research/feasibility_reports/builder.json", z.namelist())
                self.assertIn("research/live_preflight_stable.json", z.namelist())
                self.assertNotIn("profiles/nexus_api_key.json", z.namelist())

    def test_structured_multiline_record_counts_as_one_event(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "structured.eml.log"
            path.write_text(json.dumps({
                "level": "ERROR",
                "fields": {"message": "Error running mod loader", "report": "first error\nsecond error"},
            }) + "\n", encoding="utf-8")
            events = DiagnosticService().parse_file(path)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].level, "error")
            self.assertIn("second error", events[0].message)

    def test_large_log_search_uses_bounded_tail(self):
        with tempfile.TemporaryDirectory() as td:
            logs = Path(td) / "logs"; logs.mkdir()
            path = logs / "large.eml.log"
            path.write_text("old event\n" + ("filler\n" * 1000) + "latest marker\n", encoding="utf-8")
            events = DiagnosticService().search(logs, query="latest marker", max_bytes=64)
            self.assertEqual(len(events), 1)

    def test_current_success_separates_historical_errors_and_records_session(self):
        with tempfile.TemporaryDirectory() as td:
            logs = Path(td) / "logs"; logs.mkdir()
            path = logs / "latest.eml.log"
            old = json.dumps({"timestamp": "2026-09-26T10:00:00Z", "level": "ERROR", "fields": {"message": "old failure"}})
            success = json.dumps({"timestamp": "2026-09-27T10:00:00Z", "level": "INFO", "fields": {"message": "Type registry loaded successfully"}})
            path.write_text(old + "\n" + success + "\nREGISTERED|itemId=1\n", encoding="utf-8")
            summary = DiagnosticService().summarize(logs)
            self.assertEqual(summary["current_runtime_status"], "healthy")
            self.assertEqual(summary["current_errors"], 0)
            self.assertEqual(summary["historical_errors"], 1)
            self.assertEqual(summary["last_success_session"], "2026-09-27T10:00:00Z")

    def test_current_failure_without_history_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            logs = Path(td) / "logs"; logs.mkdir()
            (logs / "latest.eml.log").write_text(json.dumps({"level": "ERROR", "fields": {"message": "current failure"}}) + "\n", encoding="utf-8")
            summary = DiagnosticService().summarize(logs)
            self.assertEqual(summary["current_runtime_status"], "failed")
            self.assertEqual(summary["historical_errors"], 0)
            self.assertIn("automatic recovery", summary["recommended_action"])

    def test_native_unwind_panic_gets_safe_recovery_guidance(self):
        with tempfile.TemporaryDirectory() as td:
            logs = Path(td) / "logs"; logs.mkdir()
            (logs / "latest.eml.log").write_text(
                json.dumps({"level": "ERROR", "fields": {"message": "panic in a function that cannot unwind"}}) + "\n",
                encoding="utf-8",
            )
            guidance = DiagnosticService().summarize(logs)["recommended_action"]
            self.assertIn("quarantined", guidance)
            self.assertIn("read-only", guidance)

    def test_current_success_without_history_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            logs = Path(td) / "logs"; logs.mkdir()
            (logs / "latest.eml.log").write_text("REGISTERED|itemId=1\n", encoding="utf-8")
            summary = DiagnosticService().summarize(logs)
            self.assertEqual(summary["current_runtime_status"], "healthy")
            self.assertEqual(summary["historical_errors"], 0)

    def test_current_warnings_are_separate_from_errors(self):
        with tempfile.TemporaryDirectory() as td:
            logs = Path(td) / "logs"; logs.mkdir()
            success = json.dumps({"timestamp": "2026-09-27T10:00:00Z", "level": "INFO", "fields": {"message": "Type registry loaded successfully"}})
            warning = json.dumps({"level": "WARN", "fields": {"message": "compatibility warning"}})
            (logs / "latest.eml.log").write_text(success + "\n" + warning + "\n", encoding="utf-8")
            summary = DiagnosticService().summarize(logs)
            self.assertEqual(summary["current_runtime_status"], "degraded")
            self.assertEqual(summary["current_errors"], 0)
            self.assertEqual(summary["current_warnings"], 1)


if __name__ == "__main__":
    unittest.main()
