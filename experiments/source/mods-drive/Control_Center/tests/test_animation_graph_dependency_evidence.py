import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_animation_graph_dependency_evidence import verify


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research" / "probe_sessions" / "animation_graph_dependency_runtime_evidence_20260928.json"
BUILD = "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"


class AnimationGraphDependencyEvidenceTests(unittest.TestCase):
    def test_current_dependency_traversal_passes_without_promotion(self):
        result = verify(EVIDENCE, BUILD, "1.2")
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["verified_node_count"], 108)
        self.assertEqual(result["verified_dependency_count"], 32)
        self.assertFalse(result["promotion_ready"])

    def test_truncated_dependency_set_fails_closed(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        data["dependencies"].pop()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = verify(path, BUILD, "1.2")
        self.assertFalse(result["valid"])
        self.assertIn("dependency closure must contain 32 unique entries", result["errors"])


if __name__ == "__main__":
    unittest.main()
