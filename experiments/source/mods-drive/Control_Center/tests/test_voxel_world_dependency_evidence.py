import json, tempfile, unittest
from pathlib import Path
from tools.verify_voxel_world_dependency_map import verify

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"research"/"VOXEL_WORLD_DEPENDENCY_MAP_1076226.json"

class VoxelWorldDependencyEvidenceTests(unittest.TestCase):
    def test_current_map_passes(self):
        self.assertTrue(verify(EVIDENCE)["valid"])
    def test_scene_ownership_claim_fails_closed(self):
        data=json.loads(EVIDENCE.read_text(encoding="utf-8"));data["scene_owned_world_count"]=11
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"evidence.json";path.write_text(json.dumps(data),encoding="utf-8");result=verify(path)
        self.assertFalse(result["valid"]);self.assertIn("field mismatch: scene_owned_world_count",result["errors"])

if __name__ == "__main__": unittest.main()
