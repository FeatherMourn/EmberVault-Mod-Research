import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROBE=ROOT/"research"/"probes"/"scene_voxel_pair_probe_36234b22_1076226"

class SceneVoxelPairProbeContractTests(unittest.TestCase):
    def test_manifest_is_build_pinned_and_research_only(self):
        data=json.loads((PROBE/"mod.json").read_text(encoding="utf-8"))
        self.assertEqual(data["compatible_game_builds"],["1076226"])
        self.assertEqual(data["required_loader_api_version"],"1.3")
        self.assertEqual(data["mode"],"paired-resource-read-only")
        self.assertTrue(data["research_only"])
    def test_source_reads_exact_pair_without_mutation(self):
        source=(PROBE/"src"/"mod.lua").read_text(encoding="utf-8")
        self.assertIn("lookup('scene', 'keen::SceneResource', 0)",source)
        self.assertIn("lookup('solid', 'keen::VoxelWorldResource', 0)",source)
        self.assertIn("lookup('fog', 'keen::VoxelWorldResource', 1)",source)
        self.assertIn("content=false|created=false|registered=false|mutated=false|attached=false|world=false|save=false",source)
        self.assertNotIn("create_resource",source)
        self.assertNotIn("register_resource",source)

if __name__=="__main__":unittest.main()
