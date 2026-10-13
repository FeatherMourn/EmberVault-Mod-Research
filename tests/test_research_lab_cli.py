import json
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


if __name__ == "__main__":
    unittest.main()
