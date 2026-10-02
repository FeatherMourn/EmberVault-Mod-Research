import tempfile
import unittest
from pathlib import Path

from tools.build_visual_substitution_evidence import build


class VisualSubstitutionEvidenceBuilderTests(unittest.TestCase):
    def test_bounded_log_is_structured_without_overclaiming(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "session.log"
            log.write_text(
                'VISUAL_ASSIGNMENT|ok=true|before=donor|after=replacement\n'
                'REGISTERED|itemId=1|recipeId=2\nPLACED_ENTITY|entity-1\n',
                encoding="utf-8",
            )
            result = build(log, "probe", build_id="test-build", probe_uninstalled=True, stable_profile_restored=True)
            self.assertTrue(result["visual_assignment"]["ok"])
            self.assertEqual(result["replacement_render_model_guid"], "replacement")
            self.assertFalse(result.get("placed_object_visual_verified", False))
            self.assertEqual(result["state"], "experimental")
            self.assertEqual(result["build"], "test-build")


if __name__ == "__main__":
    unittest.main()
