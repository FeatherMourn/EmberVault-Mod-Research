import json,tempfile,unittest
from pathlib import Path
from tools.verify_water_world_donor_evidence import verify

ROOT=Path(__file__).resolve().parents[1];EVIDENCE=ROOT/"research"/"probe_sessions"/"water_world_single_donor_runtime_evidence_20260928.json";BUILD="1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"

class WaterWorldDonorEvidenceTests(unittest.TestCase):
    def test_current_read_passes_without_promotion(self):
        result=verify(EVIDENCE,BUILD,"1.3");self.assertTrue(result["valid"],result["errors"]);self.assertFalse(result["promotion_ready"])
    def test_chunk_claim_fails_closed(self):
        data=json.loads(EVIDENCE.read_text(encoding="utf-8"));data["boundary"]["chunk_content"]=True
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"e.json";p.write_text(json.dumps(data),encoding="utf-8");result=verify(p,BUILD,"1.3")
        self.assertFalse(result["valid"]);self.assertIn("prohibited boundary crossed: chunk_content",result["errors"])

if __name__=="__main__":unittest.main()
