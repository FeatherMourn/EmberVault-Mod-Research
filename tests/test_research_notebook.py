import unittest

from src.research_notebook import build_notebook


class ResearchNotebookTests(unittest.TestCase):
    def test_notebook_sorts_and_links_existing_records_only(self):
        notebook = build_notebook([
            {"id": "note-2", "kind": "comparison", "text": "Build difference", "record_ids": ["b", "a"]},
            {"id": "note-1", "kind": "note", "text": "Review later", "record_ids": ["a"]},
        ], ["a", "b"])
        self.assertEqual([entry["id"] for entry in notebook["entries"]], ["note-1", "note-2"])
        self.assertEqual(notebook["entries"][1]["record_ids"], ["a", "b"])
        self.assertTrue(notebook["read_only"])
        self.assertEqual(notebook["actions"], [])

    def test_notebook_rejects_unknown_links_and_duplicate_ids(self):
        with self.assertRaises(ValueError):
            build_notebook([{"id": "n", "kind": "note", "text": "x", "record_ids": ["missing"]}], ["known"])
        entry = {"id": "n", "kind": "note", "text": "x", "record_ids": []}
        with self.assertRaises(ValueError):
            build_notebook([entry, entry], [])


if __name__ == "__main__":
    unittest.main()
