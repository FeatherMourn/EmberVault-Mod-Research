import unittest
from pathlib import Path

from src.publication import build_web_publication
from src.research_index import load_candidates


class PublicationTests(unittest.TestCase):
    def test_publication_is_sanitized_and_review_scoped(self):
        records = load_candidates(Path(__file__).parents[1] / "research/candidates/INITIAL_CATALOG_CANDIDATES_20261004.json")
        selected = {records[0]["id"]}
        publication = build_web_publication(records, reviewed_ids=selected)
        self.assertEqual(len(publication["records"]), 1)
        item = publication["records"][0]
        self.assertTrue(item["reviewed"])
        self.assertNotIn("evidence", item)
        self.assertNotIn("source_path", item)
        self.assertEqual(item["evidence_count"], len(records[0]["evidence"]))


if __name__ == "__main__":
    unittest.main()
