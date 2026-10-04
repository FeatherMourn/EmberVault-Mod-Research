import unittest

from src.review_queue import build_review_queue


class ReviewQueueTests(unittest.TestCase):
    def test_queue_is_deterministic_and_preserves_open_contradictions(self):
        records = [{"id": "b", "state": "partially-verified", "confidence": "bounded", "open_questions": ["q"], "unsupported_claims": [], "evidence": ["b.md"]},
                   {"id": "a", "state": "confirmed", "confidence": "high", "open_questions": [], "unsupported_claims": [], "evidence": ["a.md"]}]
        contradictions = [{"id": "c-1", "record_id": "b", "claim_a": "A", "claim_b": "B", "status": "open", "resolution": ""}]
        queue = build_review_queue(records, contradictions)
        self.assertEqual([item["id"] for item in queue["records"]], ["b"])
        self.assertEqual(queue["open_contradictions"][0]["id"], "c-1")


if __name__ == "__main__":
    unittest.main()
