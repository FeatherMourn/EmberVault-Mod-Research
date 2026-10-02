import tempfile
import unittest
from pathlib import Path

from core.donor_browser import DonorBrowser


class DonorBrowserTests(unittest.TestCase):
    def test_indexes_and_searches_donors(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kfc" / "ItemInfo"; root.mkdir(parents=True)
            (root / "12345678-1234-1234-1234-1234567890ab.json").write_text(
                '{"itemId":123,"displayName":"Palm Bed","recipeIds":[1,2]}', encoding="utf-8")
            records, graph = DonorBrowser().index(root.parent)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].metadata_state, "verified")
            self.assertEqual(DonorBrowser.search(records, "palm" )[0].resource_type, "ItemInfo")
            self.assertEqual(len(DonorBrowser.search(records, field="recipeIds")), 1)
            self.assertTrue(graph.fingerprint)

    def test_type_filter_is_conservative(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kfc" / "RecipeRegistryResource"; root.mkdir(parents=True)
            (root / "recipe.json").write_text('{"recipeId":1}', encoding="utf-8")
            records, _ = DonorBrowser().index(root.parent)
            self.assertEqual(DonorBrowser.search(records, resource_type="ItemInfo"), ())


if __name__ == "__main__":
    unittest.main()
