import unittest

from src.provenance_graph import build_provenance_graph


class ProvenanceGraphTests(unittest.TestCase):
    def test_graph_is_deterministic_and_links_evidence(self):
        record = {"id": "r-1", "kind": "donor", "build_scope": ["1"], "evidence": ["source.md"],
                  "supported_claims": ["offline finding"], "unsupported_claims": [], "open_questions": ["next"]}
        graph = build_provenance_graph([record])
        self.assertEqual(graph, build_provenance_graph([record]))
        self.assertIn({"source": "record:r-1", "relation": "supported-by", "target": "evidence:source.md"}, graph["edges"])
        self.assertTrue(any(node["kind"] == "question" for node in graph["nodes"]))


if __name__ == "__main__":
    unittest.main()
