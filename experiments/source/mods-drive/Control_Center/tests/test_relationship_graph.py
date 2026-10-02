import tempfile
import unittest
from pathlib import Path

from core.relationship_graph import DonorRelationshipExplorer


class RelationshipGraphTests(unittest.TestCase):
    def test_finds_guid_and_content_hash_references(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kfc" / "ItemInfo"
            root.mkdir(parents=True)
            (root / "item.json").write_text(
                '{"modelGuid":"12345678-1234-1234-1234-1234567890ab",'
                '"iconHash":"0123456789abcdef0123456789abcdef"}', encoding="utf-8")
            graph = DonorRelationshipExplorer().scan(root.parent)
            self.assertEqual(len(graph.edges), 2)
            self.assertEqual({edge.reference_kind for edge in graph.edges}, {"guid", "content_hash"})
            self.assertTrue(graph.fingerprint)

    def test_invalid_reference_shapes_are_not_guessed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kfc"; root.mkdir()
            (root / "resource.json").write_text('{"id":"not-a-guid","short":"0123"}', encoding="utf-8")
            graph = DonorRelationshipExplorer().scan(root)
            self.assertEqual(graph.edges, ())

    def test_find_references_filters_explicit_guid_relationships(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kfc"; (root / "ItemInfo").mkdir(parents=True)
            (root / "ItemInfo" / "item.json").write_text(
                '{"objectId":"12345678-1234-1234-1234-1234567890ab",'
                '"other":"12345678-1234-1234-1234-1234567890ab"}', encoding="utf-8")
            matches = DonorRelationshipExplorer().find_references(
                root, "12345678-1234-1234-1234-1234567890ab", "objectId"
            )
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0].field, "objectId")

    def test_find_references_in_files_avoids_corpus_scan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = root / "first.json"; second = root / "second.json"
            first.write_text('{"model":"12345678-1234-1234-1234-1234567890ab"}', encoding="utf-8")
            second.write_text('{"model":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}', encoding="utf-8")
            matches = DonorRelationshipExplorer().find_references_in_files(
                [first], "12345678-1234-1234-1234-1234567890ab"
            )
            self.assertEqual(len(matches), 1)
            self.assertIn("first.json", matches[0].source)


if __name__ == "__main__":
    unittest.main()
