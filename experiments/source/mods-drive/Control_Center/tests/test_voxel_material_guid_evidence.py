import json, tempfile, unittest
from pathlib import Path
from tools.verify_voxel_material_guid_evidence import verify

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"research"/"probe_sessions"/"voxel_material_guid_type_runtime_evidence_20260928.json"
BUILD="1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"

class VoxelMaterialGuidEvidenceTests(unittest.TestCase):
    def test_current_sample_passes_without_promotion(self):
        result=verify(EVIDENCE,BUILD,"1.3");self.assertTrue(result["valid"],result["errors"]);self.assertFalse(result["promotion_ready"])
    def test_payload_claim_fails_closed(self):
        data=json.loads(EVIDENCE.read_text(encoding="utf-8"));data["boundary"]["payload"]=True
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"evidence.json";path.write_text(json.dumps(data),encoding="utf-8");result=verify(path,BUILD,"1.3")
        self.assertFalse(result["valid"]);self.assertIn("prohibited boundary crossed: payload",result["errors"])

if __name__ == "__main__": unittest.main()
