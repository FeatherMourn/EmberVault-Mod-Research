import tempfile
import unittest
from pathlib import Path

from src.analyzers import (AnalysisResult, AnalyzerSpec, PipelineRun, hash_inputs,
                           build_execution_plan, validate_offline_execution, validate_offline_inputs)


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

    def test_pipeline_run_requires_reproducibility_metadata(self):
        spec = AnalyzerSpec("kfc-inspector", "1", ("kfc3",), ("record",))
        result = AnalysisResult("kfc-inspector", "1", ("input:hash",), ("record-1",), ("1076226",),
                                "offline-static", ("No runtime behavior is established.",), True)
        run = PipelineRun(spec, result, ("record:hash",), ("parse-json",))
        self.assertTrue(run.to_dict()["read_only"])
        self.assertFalse(run.to_dict()["network_allowed"])
        with self.assertRaises(ValueError):
            PipelineRun(spec, result, (), ("parse-json",))

    def test_offline_input_validation_rejects_escape_and_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text("{}", encoding="utf-8")
            self.assertEqual(validate_offline_inputs([source], root), (source.resolve(),))
            with self.assertRaises(ValueError):
                validate_offline_inputs([root.parent / "outside.json"], root)
            with self.assertRaises(ValueError):
                validate_offline_inputs([root / "missing.json"], root)

    def test_execution_gate_is_plan_only_and_root_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / "work"
            work.mkdir()
            self.assertEqual(validate_offline_execution(approved_root=root, working_directory=work), work.resolve())
            with self.assertRaises(ValueError):
                validate_offline_execution(approved_root=root, working_directory=root.parent)
            with self.assertRaises(ValueError):
                validate_offline_execution(approved_root=root, working_directory=work, network_allowed=True)

    def test_execution_plan_is_reproducible_and_not_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / "work"
            work.mkdir()
            source = root / "input.json"
            source.write_text("{}", encoding="utf-8")
            spec = AnalyzerSpec("kfc", "1", ("json",), ("record",))
            plan = build_execution_plan(spec, [source], approved_root=root,
                                        working_directory=work, transformations=["parse-json"])
            self.assertFalse(plan["executed"])
            self.assertEqual(plan["analyzer"]["analyzer_id"], "kfc")
            self.assertEqual(len(plan["input_hashes"]), 1)


if __name__ == "__main__":
    unittest.main()
