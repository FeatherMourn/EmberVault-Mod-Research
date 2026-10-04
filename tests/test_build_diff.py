import unittest

from src.build_diff import diff_builds


class BuildDiffTests(unittest.TestCase):
    def test_diff_reports_changes_without_merging_records(self):
        records = [
            {"id": "old", "kind": "recipe", "identity": {"name": "bed"}, "build_scope": ["1"], "state": "experimental", "confidence": "low", "supported_claims": ["old"], "unsupported_claims": [], "open_questions": [], "evidence": ["old.md"]},
            {"id": "new", "kind": "recipe", "identity": {"name": "bed"}, "build_scope": ["2"], "state": "partially-verified", "confidence": "bounded", "supported_claims": ["new"], "unsupported_claims": [], "open_questions": ["q"], "evidence": ["new.md"]},
            {"id": "only-new", "kind": "donor", "identity": {"name": "chair"}, "build_scope": ["2"], "state": "experimental", "confidence": "unknown", "supported_claims": [], "unsupported_claims": [], "open_questions": [], "evidence": []},
        ]
        result = diff_builds(records, "1", "2")
        self.assertEqual([item["id"] for item in result["added"]], ["only-new"])
        self.assertEqual(result["removed"], [])
        self.assertEqual(result["changed"][0]["from_id"], "old")
        self.assertIn("confidence", result["changed"][0]["differences"])


if __name__ == "__main__":
    unittest.main()
