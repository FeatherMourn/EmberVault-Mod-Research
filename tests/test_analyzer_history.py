import unittest

from src.analyzer_history import compare_runs, filter_runs


class AnalyzerHistoryTests(unittest.TestCase):
    def setUp(self):
        self.runs = [
            {"analyzer": {"analyzer_id": "kfc", "version": "1"}, "result": {"build_scope": ["1"]}, "output_hashes": ["a"]},
            {"analyzer": {"analyzer_id": "render", "version": "1"}, "result": {"build_scope": ["2"]}, "output_hashes": ["b"]},
        ]

    def test_filter_is_identity_and_build_scoped(self):
        self.assertEqual(len(filter_runs(self.runs, analyzer_id="kfc", build="1")), 1)
        self.assertEqual(filter_runs(self.runs, analyzer_id="missing"), [])

    def test_compare_is_read_only_and_reports_changes(self):
        changed = [{**self.runs[0], "output_hashes": ["new"]}]
        report = compare_runs(self.runs[:1], changed)
        self.assertTrue(report["read_only"])
        self.assertEqual(report["changed"][0]["key"], ["kfc", "1", "1"])
