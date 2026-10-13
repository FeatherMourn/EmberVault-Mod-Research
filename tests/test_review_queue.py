import unittest

from src.review_queue import build_review_queue, evidence_score


class ReviewQueueTests(unittest.TestCase):
    def test_queue_is_deterministic_and_preserves_open_contradictions(self):
        records = [{"id": "b", "state": "partially-verified", "confidence": "bounded", "open_questions": ["q"], "unsupported_claims": [], "evidence": ["b.md"]},
                   {"id": "a", "state": "confirmed", "confidence": "high", "open_questions": [], "unsupported_claims": [], "evidence": ["a.md"]}]
        contradictions = [{"id": "c-1", "record_id": "b", "claim_a": "A", "claim_b": "B", "status": "open", "resolution": ""}]
        queue = build_review_queue(records, contradictions)
        self.assertEqual([item["id"] for item in queue["records"]], ["b"])
        self.assertEqual(queue["open_contradictions"][0]["id"], "c-1")
        self.assertEqual(queue["records"][0]["priority"], "high")
        self.assertEqual(queue["records"][0]["contradiction_count"], 1)

    def test_score_is_bounded_and_only_uses_recorded_evidence(self):
        record = {"confidence": "high", "evidence": ["a", "b", "c", "d"],
                  "open_questions": [], "unsupported_claims": []}
        self.assertEqual(evidence_score(record), 7)
        self.assertEqual(evidence_score(record, contradiction_count=2), 3)


if __name__ == "__main__":
    unittest.main()
