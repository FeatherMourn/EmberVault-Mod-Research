import json
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from src.research_lab_cli import load_records, main


class ResearchLabCliTests(unittest.TestCase):
    def test_cli_loads_json_records_and_prints_read_only_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.json"
            path.write_text(json.dumps({"records": [{"id": "r1", "kind": "donor", "identity": {},
                "state": "verified", "build_scope": ["1"], "evidence": [], "open_questions": []}]}), encoding="utf-8")
            self.assertEqual(load_records(path)[0]["id"], "r1")
            self.assertEqual(main([str(path), "--kind", "donor"]), 0)

    def test_cli_relationship_report_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.json"
            path.write_text(json.dumps({"records": [{"id": "r1", "kind": "donor", "identity": {},
                "state": "verified", "build_scope": ["1"], "evidence": ["a.md"], "open_questions": []}]}), encoding="utf-8")
            self.assertEqual(main([str(path), "--report", "relationships", "--record-id", "r1"]), 0)

    def test_cli_unified_report_accepts_local_notebook(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = root / "records.json"
            records.write_text(json.dumps({"records": [{"id": "r1", "kind": "donor", "identity": {},
                "state": "verified", "build_scope": ["1"], "evidence": [], "open_questions": []}]}), encoding="utf-8")
            notebook = root / "notebook.json"
            notebook.write_text(json.dumps({"entries": [], "read_only": True, "runtime_approval": False}), encoding="utf-8")
            self.assertEqual(main([str(records), "--report", "unified", "--notebook", str(notebook)]), 0)

    def test_cli_filters_high_priority_review_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.json"
            path.write_text(json.dumps({"records": [
                {"id": "normal", "kind": "donor", "identity": {}, "state": "verified",
                 "confidence": "high", "build_scope": ["1"], "evidence": ["a", "b", "c"], "open_questions": []},
                {"id": "urgent", "kind": "recipe", "identity": {}, "state": "blocked",
                 "confidence": "low", "build_scope": ["1"], "evidence": [], "open_questions": ["same-build"]},
            ]}), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([str(path), "--high-priority-review"]), 0)
            snapshot = json.loads(output.getvalue())
            self.assertEqual(snapshot["count"], 1)
            self.assertEqual(snapshot["records"][0]["id"], "urgent")

    def test_cli_review_priority_report_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.json"
            path.write_text(json.dumps({"records": [{"id": "r1", "kind": "donor", "identity": {},
                "state": "blocked", "build_scope": ["1"], "evidence": [], "open_questions": ["q"],
                "contradictions": []}]}), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([str(path), "--report", "review-priority"]), 0)
            report = json.loads(output.getvalue())
            self.assertTrue(report["read_only"])
            self.assertEqual(report["by_build"]["1"]["evidence_gaps"], 1)

    def test_cli_review_diff_requires_and_uses_builds(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.json"
            path.write_text(json.dumps({"records": [
                {"id": "r1", "kind": "recipe", "identity": {}, "state": "blocked",
                 "build_scope": ["1"], "evidence": [], "open_questions": ["q"], "contradictions": []},
                {"id": "r1", "kind": "recipe", "identity": {}, "state": "verified",
                 "build_scope": ["2"], "evidence": ["x"], "open_questions": [], "contradictions": []},
            ]}), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([str(path), "--report", "review-diff", "--from-build", "1", "--to-build", "2"]), 0)
            self.assertEqual(json.loads(output.getvalue())["changed"][0]["id"], "r1")

    def test_cli_creates_and_verifies_snapshot_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = root / "records.json"
            records.write_text(json.dumps({"records": [{"id": "r1", "kind": "donor", "identity": {},
                "state": "verified", "build_scope": ["1"], "evidence": [], "open_questions": []}]}), encoding="utf-8")
            bundle = root / "lab.zip"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([str(records), "--create-bundle", str(bundle)]), 0)
                self.assertEqual(main([str(records), "--verify-bundle", str(bundle)]), 0)
            self.assertTrue(bundle.is_file())
            self.assertIn('"recovery": "verify-before-extract"', output.getvalue())

    def test_cli_prunes_bundle_directory_without_catalog_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.zip").write_bytes(b"a")
            (root / "b.zip").write_bytes(b"b")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["--prune-bundles", str(root), "--keep", "1"]), 0)
            result = json.loads(output.getvalue())
            self.assertEqual(len(result["removed"]), 1)


if __name__ == "__main__":
    unittest.main()
