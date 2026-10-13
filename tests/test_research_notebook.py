import unittest

from src.research_notebook import build_notebook, compare_notebooks, experiment_summary


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

    def test_notebook_comparison_and_experiment_summary_are_read_only(self):
        previous = build_notebook([{ "id": "n1", "kind": "note", "text": "old", "record_ids": ["a"] }], ["a"])
        current = build_notebook([
            {"id": "n1", "kind": "note", "text": "new", "record_ids": ["a"]},
            {"id": "e1", "kind": "experiment-reference", "text": "offline package check", "record_ids": ["a"]},
        ], ["a"])
        comparison = compare_notebooks(previous, current)
        self.assertEqual(comparison["added"], ["e1"])
        self.assertEqual(comparison["changed"], ["n1"])
        summary = experiment_summary(current, "a")
        self.assertEqual(summary["experiments"][0]["id"], "e1")
        self.assertEqual(summary["actions"], [])


if __name__ == "__main__":
    unittest.main()
