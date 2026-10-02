import json
import tempfile
import unittest
from pathlib import Path
from tools.verify_visual_substitution_batch import validate

class VisualSubstitutionBatchVerifierTests(unittest.TestCase):
    def test_generated_plan_is_valid(self):
        path = Path(__file__).parents[1] / "research" / "probe_sessions" / "visual_substitution_batch_plan_20260928.json"
        self.assertEqual(validate(path), [])

    def test_duplicate_item_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(__file__).parents[1] / "research" / "probe_sessions" / "visual_substitution_batch_plan_20260928.json"
            data = json.loads(source.read_text())
            data["runs"][1]["item_id"] = data["runs"][0]["item_id"]
            path = Path(directory) / "plan.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any("item_id" in error for error in validate(path)))

if __name__ == "__main__":
    unittest.main()
