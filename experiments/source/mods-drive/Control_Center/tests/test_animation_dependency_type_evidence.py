import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_animation_dependency_type_evidence import verify


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research" / "probe_sessions" / "animation_dependency_type_runtime_evidence_20260928.json"
BUILD = "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"


class AnimationDependencyTypeEvidenceTests(unittest.TestCase):
    def test_current_type_resolution_passes_without_promotion(self):
        result = verify(EVIDENCE, BUILD, "1.3")
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["resolved_guids"], 32)
        self.assertEqual(result["resource_matches"], 42)
        self.assertFalse(result["promotion_ready"])

    def test_unresolved_dependency_fails_closed(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        data["summary"]["resolved_guids"] = 31
        data["summary"]["unresolved_guids"] = 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = verify(path, BUILD, "1.3")
        self.assertFalse(result["valid"])
        self.assertIn("resolution summary mismatch", result["errors"])
