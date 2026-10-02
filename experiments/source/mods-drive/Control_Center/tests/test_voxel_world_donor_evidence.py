import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_voxel_world_donor_evidence import verify


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research" / "probe_sessions" / "voxel_world_single_donor_runtime_evidence_20260928.json"
BUILD = "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"


class VoxelWorldDonorEvidenceTests(unittest.TestCase):
    def test_current_readback_passes_without_promotion(self):
        result = verify(EVIDENCE, BUILD, "1.3")
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["verified_voxel_level_count"], 7)
        self.assertFalse(result["promotion_ready"])

    def test_world_attachment_claim_fails_closed(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        data["prohibited_boundaries"]["world"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = verify(path, BUILD, "1.3")
        self.assertFalse(result["valid"])
        self.assertIn("prohibited boundary crossed: world", result["errors"])


if __name__ == "__main__":
    unittest.main()
