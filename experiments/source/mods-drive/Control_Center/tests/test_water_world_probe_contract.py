import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROBE=ROOT/"research"/"probes"/"water_world_single_donor_probe_36234b22_1076226"

class WaterWorldProbeContractTests(unittest.TestCase):
    def test_manifest_is_bounded_and_research_only(self):
        data=json.loads((PROBE/"mod.json").read_text(encoding="utf-8"))
        self.assertEqual(data["mode"],"single-resource-read-only")
        self.assertEqual(data["required_loader_api_version"],"1.3")
        self.assertTrue(data["research_only"])
    def test_source_excludes_chunk_and_mutation_paths(self):
        source=(PROBE/"src"/"mod.lua").read_text(encoding="utf-8")
        self.assertIn("keen::WaterWorldResource",source)
        self.assertIn("chunk_content=false|created=false|registered=false|mutated=false|attached=false|world=false|save=false",source)
        self.assertNotIn("WaterChunkResource",source)
        self.assertNotIn("create_resource",source)
        self.assertNotIn("register_resource",source)

if __name__=="__main__":unittest.main()
