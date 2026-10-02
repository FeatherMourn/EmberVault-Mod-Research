import json
import tempfile
import unittest
from pathlib import Path
from tools.verify_animation_graph_attachment_evidence import verify

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research" / "probe_sessions" / "animation_graph_npc_attachment_runtime_evidence_20260928.json"
BUILD = "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"

class AnimationGraphAttachmentEvidenceTests(unittest.TestCase):
    def test_current_owner_attachment_passes_without_promotion(self):
        result = verify(EVIDENCE, BUILD, "1.3"); self.assertTrue(result["valid"], result["errors"]); self.assertTrue(result["owner_attachment_verified"]); self.assertFalse(result["promotion_ready"])

    def test_save_boundary_claim_is_rejected(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8")); data["prohibited_boundaries"]["save"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"; path.write_text(json.dumps(data), encoding="utf-8"); result = verify(path, BUILD, "1.3")
        self.assertFalse(result["valid"]); self.assertIn("prohibited boundary was crossed", result["errors"])
