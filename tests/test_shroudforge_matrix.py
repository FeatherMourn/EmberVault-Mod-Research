import json
import unittest
from pathlib import Path


class ShroudForgeMatrixTests(unittest.TestCase):
    def test_matrix_is_read_only_and_runtime_bounded(self):
        path = Path(__file__).parents[1] / "research/external/SHROUDFORGE_CAPABILITY_MATRIX_20261013.json"
        matrix = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(matrix["read_only"])
        self.assertFalse(matrix["runtime_approval"])
        self.assertEqual(len(matrix["capabilities"]), 9)
        self.assertTrue(all(item["evidence_boundary"] for item in matrix["capabilities"]))

    def test_matrix_covers_downstream_consumers(self):
        path = Path(__file__).parents[1] / "research/external/SHROUDFORGE_CAPABILITY_MATRIX_20261013.json"
        areas = {item["area"]: set(item["embervault_use"]) for item in json.loads(path.read_text())["capabilities"]}
        self.assertIn("Content Creator", areas["settings-schemas"])
        self.assertIn("Mod Manager", areas["update-staging"])
        self.assertIn("Troubleshooter", areas["multiplayer-routing"])


if __name__ == "__main__":
    unittest.main()
