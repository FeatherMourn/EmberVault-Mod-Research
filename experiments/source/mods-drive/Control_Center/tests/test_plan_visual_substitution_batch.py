import unittest
from pathlib import Path
from tools.plan_visual_substitution_batch import build_plan

class VisualSubstitutionBatchTests(unittest.TestCase):
    def test_plan_is_deterministic_and_isolated(self):
        matrix = Path("research/templates/visual_substitution_probe_matrix.json")
        first, second = build_plan(matrix, "test"), build_plan(matrix, "test")
        self.assertEqual(first["matrix_sha256_prefix"], second["matrix_sha256_prefix"])
        self.assertEqual(first["runs"], second["runs"])
        self.assertFalse(first["execution_policy"]["stable_profile_allowed"])
        self.assertEqual(len(first["runs"]), 4)
        self.assertEqual(len({run["item_id"] for run in first["runs"]}), 4)

    def test_plan_requires_explicit_save_approval(self):
        plan = build_plan(Path("research/templates/visual_substitution_probe_matrix.json"), "test")
        self.assertTrue(all(run["save_requires_explicit_approval"] for run in plan["runs"]))

if __name__ == "__main__":
    unittest.main()
