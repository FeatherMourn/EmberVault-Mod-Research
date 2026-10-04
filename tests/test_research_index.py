import json
import tempfile
import unittest
from pathlib import Path

from src.research_index import load_candidates, load_manifest, missing_evidence, search


class ResearchIndexTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).parents[1] / "research" / "candidates" / "INITIAL_CATALOG_CANDIDATES_20261004.json"
        self.records = load_candidates(self.path)
        self.manifest = load_manifest(Path(__file__).parents[1] / "research" / "INTAKE_MANIFEST_20261004.json")

    def test_loads_unique_candidate_records(self):
        self.assertEqual(len(self.records), 8)
        self.assertEqual(len({record["id"] for record in self.records}), 8)

    def test_search_filters_without_mutation(self):
        before = json.dumps(self.records, sort_keys=True)
        results = search(self.records, "recipe", state="blocked")
        self.assertEqual([record["kind"] for record in results], ["donor-recipe"])
        self.assertEqual(before, json.dumps(self.records, sort_keys=True))

    def test_search_filters_build_and_kind(self):
        results = search(self.records, build="1076226", kind="render-model")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["identity"]["guid"], "1ac410c2-c85e-4172-95eb-19b5b593118d")

    def test_search_filters_confidence_and_evidence_gaps(self):
        results = search(self.records, confidence="high-for-recorded-inputs", has_open_questions=True)
        self.assertEqual([record["kind"] for record in results], ["offline-catalog"])

    def test_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            payload = {"schema_version": 1, "records": [self.records[0], self.records[0]]}
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_candidates(path)

    def test_candidate_evidence_is_in_manifest(self):
        self.assertEqual(missing_evidence(self.records, self.manifest), [])

    def test_reports_untracked_evidence(self):
        records = [dict(self.records[0], evidence=["research/promoted/missing.md"])]
        self.assertEqual(missing_evidence(records, self.manifest), ["research/promoted/missing.md"])


if __name__ == "__main__":
    unittest.main()
