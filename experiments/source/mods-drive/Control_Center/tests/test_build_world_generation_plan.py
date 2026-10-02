import json
import tempfile
import unittest
from pathlib import Path

from tools.build_world_generation_plan import build
from tools.validate_world_generation_plan import validate

class WorldGenerationPlanTests(unittest.TestCase):
    def test_builds_pinned_safe_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(json.dumps(build("1076226", "36234b22-85f2-4001-ac56-002b379d0d88", "Test")), encoding="utf-8")
            result = validate(path, "1076226")
            self.assertTrue(result["valid"], result["errors"])
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["feature_state"], "research-only")
            self.assertEqual(len(data["layers"]), 2)

    def test_plan_operations_are_unapproved(self):
        plan = build("1076226", "36234b22-85f2-4001-ac56-002b379d0d88", "Test")
        self.assertTrue(all(item["approved"] is False for item in plan["operations"]))

if __name__ == "__main__":
    unittest.main()
