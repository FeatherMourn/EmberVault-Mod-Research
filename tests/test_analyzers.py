import tempfile
import unittest
from pathlib import Path

from src.analyzers import AnalysisResult, AnalyzerSpec, hash_inputs


class AnalyzerTests(unittest.TestCase):
    def test_spec_is_read_only_and_result_is_bounded(self):
        spec = AnalyzerSpec("kfc-inspector", "1", ("kfc3",), ("rendermodel",))
        self.assertTrue(spec.read_only)
        result = AnalysisResult("kfc-inspector", "1", ("a:hash",), ("record-1",), ("1076226",),
                                "offline-static", ("No runtime behavior is established.",), True)
        self.assertEqual(result.to_dict()["evidence_type"], "offline-static")
        with self.assertRaises(ValueError):
            AnalysisResult("x", "1", (), (), (), "runtime", (), False)

    def test_input_hashes_are_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "a.bin"
            second = Path(directory) / "b.bin"
            first.write_bytes(b"a")
            second.write_bytes(b"b")
            self.assertEqual(hash_inputs([second, first]), hash_inputs([first, second]))


if __name__ == "__main__":
    unittest.main()
