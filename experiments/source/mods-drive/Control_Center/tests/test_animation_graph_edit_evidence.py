import json
import tempfile
import unittest
from pathlib import Path
from tools.verify_animation_graph_edit_evidence import verify

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"research"/"probe_sessions"/"animation_graph_idle_variant_runtime_evidence_20260928.json"
BUILD="1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"

class AnimationGraphEditEvidenceTests(unittest.TestCase):
    def test_structural_edit_passes_without_behavior_promotion(self):
        result=verify(EVIDENCE,BUILD,"1.3");self.assertTrue(result["valid"],result["errors"]);self.assertTrue(result["structural_edit_verified"]);self.assertFalse(result["visible_behavior_verified"])
    def test_behavior_overclaim_fails_closed(self):
        data=json.loads(EVIDENCE.read_text(encoding="utf-8"));data["visible_behavior_observed"]=True
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"evidence.json";path.write_text(json.dumps(data),encoding="utf-8");result=verify(path,BUILD,"1.3")
        self.assertFalse(result["valid"]);self.assertIn("unsubstantiated visible behavior claim",result["errors"])
