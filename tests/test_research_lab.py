import unittest

from src.research_lab import build_lab_snapshot, evidence_navigation, record_detail, relationship_view


class ResearchLabTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            {"id": "donor-a", "kind": "donor", "identity": {"name": "Bed"}, "build_scope": ["1"],
             "state": "verified", "confidence": "bounded", "evidence": ["a.md"], "open_questions": [], "contradictions": []},
            {"id": "recipe-b", "kind": "recipe", "identity": {"name": "Bed recipe"}, "build_scope": ["2"],
             "state": "blocked", "confidence": "low", "evidence": ["b.md"], "open_questions": ["same-build"], "contradictions": [{"id": "c1"}]},
        ]

    def test_snapshot_filters_authoritative_records_read_only(self):
        snapshot = build_lab_snapshot(self.records, kind="recipe", has_open_questions=True)
        self.assertEqual(snapshot["count"], 1)
        self.assertEqual(snapshot["records"][0]["id"], "recipe-b")
        self.assertTrue(snapshot["read_only"])
        self.assertEqual(snapshot["actions"], [])
        self.assertFalse(snapshot["records"][0]["runtime_approval"])

    def test_detail_preserves_record_and_blocks_runtime_approval(self):
        detail = record_detail(self.records[0])
        self.assertEqual(detail["record"]["id"], "donor-a")
        self.assertTrue(detail["read_only"])
        self.assertEqual(detail["actions"], [])
        self.assertFalse(detail["runtime_approval"])

    def test_relationship_and_evidence_views_are_read_only(self):
        relationships = relationship_view(self.records, "recipe-b")
        self.assertTrue(any(node["kind"] == "evidence" for node in relationships["nodes"]))
        self.assertEqual(relationships["actions"], [])
        evidence = evidence_navigation(self.records, "b.md")
        self.assertEqual(evidence["records"][0]["id"], "recipe-b")
        self.assertEqual(evidence["actions"], [])


if __name__ == "__main__":
    unittest.main()
