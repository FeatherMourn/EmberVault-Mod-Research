import json
import sys
import tempfile
import unittest
from pathlib import Path

from tools.build_recipe_customization_probe import main


class RecipeCustomizationProbeGeneratorTests(unittest.TestCase):
    def test_generator_emits_safe_research_probe(self):
        root = Path(__file__).resolve().parents[1]
        template = root / "research" / "probes" / "bed_clone_injection_1076226" / "src" / "mod.lua"
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "recipe_probe"
            old = sys.argv
            try:
                sys.argv = ["build_recipe_customization_probe.py", str(template), str(output), "--new-item-id", "501", "--new-recipe-id", "502"]
                self.assertEqual(main(), 0)
            finally:
                sys.argv = old
            manifest = json.loads((output / "mod.json").read_text(encoding="utf-8"))
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertEqual(manifest["feature_state"], "research-only")
            self.assertEqual(manifest["new_item_id"], 501)
            self.assertEqual(manifest["new_recipe_id"], 502)
            self.assertIn("knowledgeRequirement_clear", source)
            self.assertTrue((output / "src" / "kfc_content_registry.lua").is_file())


if __name__ == "__main__":
    unittest.main()
