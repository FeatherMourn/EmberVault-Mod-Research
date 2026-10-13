import unittest

from src.resource_graph import build_resource_graph


class ResourceGraphTests(unittest.TestCase):
    def test_links_explicit_identity_without_inference(self):
        records = [
            {"id": "kfc-1", "kind": "kfc3-metadata", "identity": {"guid": "g-1"}},
            {"id": "model-1", "kind": "rendermodel-metadata", "identity": {"guid": "g-1"}},
        ]
        graph = build_resource_graph(records)
        self.assertTrue(graph["read_only"])
        self.assertFalse(graph["runtime_approval"])
        self.assertIn({"source": "record:kfc-1", "relation": "shares-guid", "target": "identity:guid:g-1"}, graph["edges"])
        self.assertIn({"source": "record:model-1", "relation": "shares-guid", "target": "identity:guid:g-1"}, graph["edges"])
        self.assertEqual(graph, build_resource_graph(list(reversed(records))))


if __name__ == "__main__":
    unittest.main()
