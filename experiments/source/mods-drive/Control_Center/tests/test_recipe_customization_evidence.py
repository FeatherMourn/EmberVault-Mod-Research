import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_recipe_customization_evidence import verify


class RecipeCustomizationEvidenceTests(unittest.TestCase):
    def _write(self, root: Path, **overrides):
        data = {
            "schema": "control_center.recipe_knowledge_requirement_runtime_evidence.v2",
            "feature_state": "research-only",
            "clone_item_id": 10,
            "clone_recipe_id": 11,
            "evidence": {
                "craftingDuration": True,
                "output_count": True,
                "input_itemStack_count": True,
                "typed_workshopId_replacement": True,
                "requiredProps_clear_on_clone": True,
                "knowledgeRequirement_clear_on_clone": True,
                "clone_registration_reached": True,
                "panic_or_loader_error": False,
            },
            "cleanup": {"game_stopped": True, "probe_uninstalled": True, "stable_profile_restored": True},
            "limitations": ["craft persistence is not yet verified"],
        }
        data.update(overrides)
        path = root / "evidence.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_valid_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertTrue(verify(self._write(Path(td)))['valid'])

    def test_panic_or_missing_cleanup_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = self._write(root)
            data = json.loads(path.read_text())
            data["evidence"]["panic_or_loader_error"] = True
            data["cleanup"]["stable_profile_restored"] = False
            path.write_text(json.dumps(data), encoding="utf-8")
            result = verify(path)
            self.assertFalse(result['valid'])
            self.assertIn("panic_or_loader_error", " ".join(result['errors']))
            self.assertIn("stable_profile_restored", " ".join(result['errors']))


if __name__ == "__main__":
    unittest.main()
