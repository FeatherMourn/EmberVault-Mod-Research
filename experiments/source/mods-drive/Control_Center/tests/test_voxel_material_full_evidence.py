import json,tempfile,unittest
from pathlib import Path
from tools.verify_voxel_material_full_evidence import verify

ROOT=Path(__file__).resolve().parents[1];EVIDENCE=ROOT/"research"/"probe_sessions"/"voxel_material_full_metadata_runtime_evidence_20260928.json";BUILD="1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"

class VoxelMaterialFullEvidenceTests(unittest.TestCase):
    def test_complete_classification_passes_without_promotion(self):
        result=verify(EVIDENCE,BUILD,"1.3");self.assertTrue(result["valid"],result["errors"]);self.assertEqual(result["classified_guid_count"],198);self.assertFalse(result["promotion_ready"])
    def test_semantic_overclaim_fails_closed(self):
        data=json.loads(EVIDENCE.read_text(encoding="utf-8"));data["archive_correlation"]["semantic_role_verified"]=True
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"e.json";p.write_text(json.dumps(data),encoding="utf-8");result=verify(p,BUILD,"1.3")
        self.assertFalse(result["valid"]);self.assertIn("semantic role is overclaimed",result["errors"])

if __name__=="__main__":unittest.main()
