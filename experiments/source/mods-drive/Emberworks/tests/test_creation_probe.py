import unittest
from pathlib import Path


class CreationProbeTests(unittest.TestCase):
    def test_probe_is_isolated_and_unreferenced(self):
        root = Path(__file__).parents[1] / "runtime_mods" / "emberworks_resource_creation_probe"
        manifest = (root / "mod.json").read_text(encoding="utf-8")
        source = (root / "src" / "mod.lua").read_text(encoding="utf-8")
        self.assertIn("emberworks_resource_creation_probe", manifest)
        self.assertIn("create_resource", source)
        self.assertIn("VoxelModelResource", source)
        self.assertIn("RenderModel", source)
        self.assertIn("ItemRegistryResource", source)
        self.assertIn("item_registry_insert_result", source)
        self.assertIn("RecipeRegistryResource", source)
        self.assertIn("recipe_registry_insert_result", source)
        self.assertIn("ui_recipe_link_hits", source)
        self.assertNotIn("register_resource", source)
        self.assertNotIn("create_content", source)


if __name__ == "__main__":
    unittest.main()
