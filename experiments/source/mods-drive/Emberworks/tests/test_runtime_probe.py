import json
import unittest
from pathlib import Path


class RuntimeProbeTests(unittest.TestCase):
    def test_worldwright_probe_is_observe_only(self):
        root = Path(__file__).parents[1]
        manifest = json.loads((root / "runtime_mods/emberworks_worldwright_probe/mod.json").read_text(encoding="utf-8"))
        source = (root / "runtime_mods/emberworks_worldwright_probe/src/mod.lua").read_text(encoding="utf-8")
        self.assertEqual(manifest["capabilities"], ["patch", "export", "runtime-register-dll"])
        self.assertNotIn("assets.create_resource(", source)
        self.assertNotIn("assets.create_content(", source)
        self.assertIn("absolute_register_dll", source)
        self.assertIn("get_all_resources", source)
        self.assertIn("game.guid", source)
        self.assertIn("keen::VoxelModelResource", source)
        self.assertIn("keen::BuildableObject", source)
        self.assertIn("create_resource", source)
        self.assertIn("register_resource", source)
        self.assertIn("loader.is_client", source)
        self.assertIn("loader.features.runtime.dll", source)


if __name__ == "__main__":
    unittest.main()
