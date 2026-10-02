import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROBE=ROOT/"research"/"probes"/"scene_resource_family_metadata_probe_36234b22_1076226"

class SceneResourceFamilyProbeContractTests(unittest.TestCase):
    def test_manifest_is_metadata_only(self):
        data=json.loads((PROBE/"mod.json").read_text(encoding="utf-8"))
        self.assertEqual(data["mode"],"metadata-only-read-only")
        self.assertEqual(data["required_loader_api_version"],"1.3")
        self.assertTrue(data["research_only"])
    def test_source_has_no_payload_or_mutation_route(self):
        source=(PROBE/"src"/"mod.lua").read_text(encoding="utf-8")
        self.assertIn("get_resource_metadata_by_guid(GUID)",source)
        self.assertIn("keen::VoxelWorldChunkResource",source)
        self.assertIn("keen::SceneEntityChunkResource",source)
        self.assertIn("payload=false|created=false|registered=false|mutated=false|attached=false|world=false|save=false",source)
        self.assertNotIn("get_resource(",source)
        self.assertNotIn("create_resource",source)

if __name__=="__main__":unittest.main()
