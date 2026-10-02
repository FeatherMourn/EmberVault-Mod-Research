import unittest
from pathlib import Path
from tools.verify_visual_substitution_matrix import validate

class VisualSubstitutionMatrixTests(unittest.TestCase):
    def test_shipped_matrix_is_safe(self):
        path = Path(__file__).parents[1] / "research" / "templates" / "visual_substitution_probe_matrix.json"
        self.assertEqual(validate(path), [])

    def test_matrix_rejects_stable_profile(self):
        import json, tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.json"
            data = json.loads((Path(__file__).parents[1] / "research" / "templates" / "visual_substitution_probe_matrix.json").read_text())
            data["safety"]["stable_profile_allowed"] = True
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any("stable_profile_allowed" in error for error in validate(path)))
