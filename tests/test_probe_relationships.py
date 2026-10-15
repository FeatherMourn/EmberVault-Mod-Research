import unittest

from src.probe_relationships import build_inventory_relationships


class ProbeRelationshipTests(unittest.TestCase):
    def test_builds_deterministic_type_and_guid_edges(self):
        result = build_inventory_relationships([
            {"id": "eml:type:item", "kind": "eml-resource-type", "identity": {"resource_type": "keen::ItemInfo"}},
            {"id": "eml:resource:g1:keen::ItemInfo:0", "kind": "eml-resource-observation", "identity": {"guid": "g1", "resource_type": "keen::ItemInfo", "part_index": "0"}},
        ])
        self.assertEqual(len(result["edges"]), 3)
        self.assertTrue(result["read_only"])
        self.assertEqual(result, build_inventory_relationships(list(reversed([
            {"id": "eml:type:item", "kind": "eml-resource-type", "identity": {"resource_type": "keen::ItemInfo"}},
            {"id": "eml:resource:g1:keen::ItemInfo:0", "kind": "eml-resource-observation", "identity": {"guid": "g1", "resource_type": "keen::ItemInfo", "part_index": "0"}},
        ]))))


if __name__ == "__main__":
    unittest.main()
