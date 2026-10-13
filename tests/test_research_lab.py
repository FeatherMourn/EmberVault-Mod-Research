import unittest

from src.research_lab import (build_comparison_view, build_lab_snapshot, contradiction_review_view,
                               content_creator_view, evidence_navigation, facet_summary, record_detail, relationship_view)


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

    def test_facets_surface_review_gaps_without_actions(self):
        facets = facet_summary(self.records)
        self.assertEqual(facets["by_kind"], {"donor": 1, "recipe": 1})
        self.assertEqual(facets["by_build"], {"1": 1, "2": 1})
        self.assertEqual(facets["evidence_gaps"], ["recipe-b"])
        self.assertEqual(facets["contradiction_records"], ["recipe-b"])
        self.assertEqual(facets["actions"], [])

    def test_build_and_contradiction_views_preserve_review_boundaries(self):
        comparison = build_comparison_view(self.records, "1", "2")
        self.assertEqual(comparison["from_build"], "1")
        self.assertTrue(comparison["read_only"])
        review = contradiction_review_view(self.records, [{"id": "c1", "status": "open"}])
        self.assertEqual(review["open_contradictions"][0]["id"], "c1")
        self.assertEqual(review["actions"], [])

    def test_content_creator_view_preserves_limits_and_no_runtime_approval(self):
        handoff = content_creator_view(self.records, ids=["recipe-b"], contradictions=[
            {"id": "c1", "record_id": "recipe-b", "status": "open", "claim_a": "A", "claim_b": "B"}
        ])
        self.assertEqual(handoff["records"][0]["id"], "recipe-b")
        self.assertEqual(handoff["application_state"], "design-only")
        self.assertFalse(handoff["runtime_approval"])
        self.assertEqual(handoff["actions"], [])


if __name__ == "__main__":
    unittest.main()
