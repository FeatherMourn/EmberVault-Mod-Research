import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from tools.build_registered_visual_probe import main


class RegisteredVisualProbeTests(unittest.TestCase):
    def test_generator_injects_assignment_and_keeps_research_only_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            template = root / "template.lua"
            template.write_text("local NEW_ITEM_ID = 3987654321\nlocal NEW_RECIPE_ID = 3987654322\nlocal clone = clone_or_error\n", encoding="utf-8")
            output = root / "probe"
            import sys
            old = sys.argv
            try:
                sys.argv = ["build_registered_visual_probe.py", str(template), str(output), "11", "12", "model-guid"]
                self.assertEqual(main(), 0)
            finally:
                sys.argv = old
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertIn("VISUAL_ASSIGNMENT", source)
            self.assertIn("replacement_equals_donor", source)
            self.assertIn("NEW_ITEM_ID = 11", source)
            self.assertIn("NEW_RECIPE_ID = 12", source)
            self.assertEqual(__import__("json").loads((output / "mod.json").read_text())["feature_state"], "research-only")

    def test_generator_can_add_guarded_material_texture_and_color_assignments(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            template = root / "template.lua"
            template.write_text("local NEW_ITEM_ID = 3987654321\nlocal NEW_RECIPE_ID = 3987654322\nlocal clone = clone_or_error\n", encoding="utf-8")
            output = root / "probe"
            import sys
            old = sys.argv
            try:
                sys.argv = ["build_registered_visual_probe.py", str(template), str(output), "11", "12", "model-guid", "--material-guid", "material-guid", "--texture-guid", "texture-guid", "--color", "#AABBCC"]
                self.assertEqual(main(), 0)
            finally:
                sys.argv = old
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertIn("VISUAL_MATERIAL_ASSIGNMENT", source)
            self.assertIn("VISUAL_TEXTURE_ASSIGNMENT", source)
            self.assertIn("VISUAL_COLOR_ASSIGNMENT", source)

    def test_generator_does_not_duplicate_existing_model_assignment(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            template = root / "template.lua"
            template.write_text(
                "local NEW_ITEM_ID = 3987654321\nlocal NEW_RECIPE_ID = 3987654322\n"
                "local clone = clone_or_error\nlocal replacement_model_guid = 'existing'\n",
                encoding="utf-8")
            output = root / "probe"
            import sys
            old = sys.argv
            try:
                sys.argv = ["build_registered_visual_probe.py", str(template), str(output), "11", "12", "model-guid", "--material-guid", "material-guid"]
                self.assertEqual(main(), 0)
            finally:
                sys.argv = old
            source = (output / "src" / "mod.lua").read_text(encoding="utf-8")
            self.assertEqual(source.count("local replacement_model_guid"), 1)
            self.assertIn("VISUAL_MATERIAL_ASSIGNMENT", source)

    def test_generator_rejects_invalid_color(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            template = root / "template.lua"
            template.write_text("local NEW_ITEM_ID = 3987654321\nlocal NEW_RECIPE_ID = 3987654322\nlocal clone = clone_or_error\n", encoding="utf-8")
            import sys
            old = sys.argv
            try:
                sys.argv = ["build_registered_visual_probe.py", str(template), str(root / "probe"), "11", "12", "model-guid", "--color", "blue"]
                with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                    main()
            finally:
                sys.argv = old

