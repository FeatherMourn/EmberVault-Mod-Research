import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VisualCandidateSearchTests(unittest.TestCase):
    def test_ranks_complete_shape_before_incomplete_shape(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            donor = root / "donor.json"
            candidates = root / "candidates"
            candidates.mkdir()
            donor.write_text(json.dumps({"meshes": [{"materialIndex": 0}, {"materialIndex": 1}], "lods": [{"meshCount": 2}]}))
            (candidates / "incomplete.json").write_text(json.dumps({"meshes": [{"materialIndex": 0}], "lods": [{"meshCount": 1}]}))
            (candidates / "complete.json").write_text(json.dumps({"meshes": [{"materialIndex": 0}, {"materialIndex": 1}], "lods": [{"meshCount": 2}]}))
            result = subprocess.run(
                [sys.executable, "tools/find_visual_candidates.py", str(donor), str(candidates), "--limit", "2"],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            report = json.loads(result.stdout)
            self.assertEqual(report["compatible_count"], 1)
            self.assertTrue(report["candidates"][0]["graph_compatible"])
            self.assertTrue(report["candidates"][0]["path"].endswith("complete.json"))


if __name__ == "__main__":
    unittest.main()
