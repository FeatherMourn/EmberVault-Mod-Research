from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "research" / "probes" / "voxel_world_single_donor_probe_1076226"


class VoxelWorldProbeContractTests(unittest.TestCase):
    def test_manifest_is_build_pinned_and_research_only(self):
        manifest = json.loads((PROBE / "mod.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["compatible_game_builds"], ["1076226"])
        self.assertEqual(manifest["required_loader_api_version"], "1.3")
        self.assertEqual(manifest["feature_state"], "research-only")
        self.assertEqual(manifest["mode"], "single-resource-read-only")

    def test_probe_is_bounded_and_fail_closed(self):
        source = (PROBE / "src" / "mod.lua").read_text(encoding="utf-8")
        self.assertIn("keen::VoxelWorldResource", source)
        self.assertIn("022bd475-089a-43b8-b49a-2bcf2f0cd84f", source)
        self.assertIn("game.assets.get_resource(GUID, TYPE, 0)", source)
        self.assertIn("single_voxel_world_payload_read_complete", source)
        self.assertIn(
            "created=false|registered=false|mutated=false|attached=false|world=false|save=false",
            source,
        )
        self.assertNotIn("game.assets.create_resource", source)
        self.assertNotIn("game.assets.register_resource", source)
        self.assertNotIn("game.assets.create", source)
        self.assertNotIn("game.assets.register", source)


if __name__ == "__main__":
    unittest.main()
