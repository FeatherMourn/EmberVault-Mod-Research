import json
import tempfile
import unittest
from pathlib import Path
from tools.verify_animation_graph_clone_evidence import verify

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research" / "probe_sessions" / "animation_graph_identity_clone_runtime_evidence_20260928.json"
BUILD = "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"

class AnimationGraphCloneEvidenceTests(unittest.TestCase):
    def test_current_identity_clone_passes_without_promotion(self):
        result = verify(EVIDENCE, BUILD, "1.3")
        self.assertTrue(result["valid"], result["errors"]); self.assertTrue(result["identity_clone_verified"]); self.assertFalse(result["promotion_ready"])

    def test_dependency_parity_failure_is_rejected(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8")); data["parity"]["dependencies"] = False
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"; path.write_text(json.dumps(data), encoding="utf-8"); result = verify(path, BUILD, "1.3")
        self.assertFalse(result["valid"]); self.assertIn("clone parity mismatch", result["errors"])
