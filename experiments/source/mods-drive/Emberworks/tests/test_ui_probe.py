import unittest
from pathlib import Path


class UIProbeTests(unittest.TestCase):
    def test_probe_is_read_only_and_targets_ui_registry(self):
        root = Path(__file__).parents[1] / "runtime_mods" / "emberworks_ui_probe"
        source = (root / "src" / "mod.lua").read_text(encoding="utf-8")
        self.assertIn("keen::FbUiBundle", source)
        self.assertIn("probe_recipe_hits", source)
        self.assertNotIn("table.insert", source)


if __name__ == "__main__":
    unittest.main()
