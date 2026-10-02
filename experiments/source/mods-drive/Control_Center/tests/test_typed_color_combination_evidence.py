import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_typed_color_combination_evidence import verify


BUILD = "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"


class TypedColorCombinationEvidenceTests(unittest.TestCase):
    def test_current_evidence_is_valid_and_not_promoted(self):
        path = Path("research/probe_sessions/typed_color_combination_runtime_evidence_20260930.json")
        result = verify(path, BUILD)
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["promotion_ready"])

    def test_short_numeric_build_matches_full_eml_build(self):
        path = Path("research/probe_sessions/typed_color_combination_runtime_evidence_20260930.json")
        result = verify(path, "1076226")
        self.assertTrue(result["valid"], result)

    def test_visual_claim_is_rejected(self):
        data = json.loads(Path("research/probe_sessions/typed_color_combination_runtime_evidence_20260930.json").read_text())
        data["visual_evidence"]["placed_object_visible"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(data))
            result = verify(path, BUILD)
        self.assertFalse(result["valid"])
        self.assertTrue(any("visible recoloring" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
