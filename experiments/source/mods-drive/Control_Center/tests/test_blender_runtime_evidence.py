import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.verify_blender_runtime_evidence import validate


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research" / "probe_sessions" / "blender_render_model_round_trip_runtime_evidence_20260928.json"


class BlenderRuntimeEvidenceTests(unittest.TestCase):
    def test_current_partial_evidence_is_valid(self):
        result = validate(EVIDENCE)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["state"], "experimental")
        self.assertFalse(result["promotion_ready"])

    def test_promotion_requires_visual_proof(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        data["promotion_ready"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = validate(path)
        self.assertFalse(result["valid"])
        self.assertTrue(any("promotion_ready" in error for error in result["errors"]))

    def test_standalone_cli(self):
        completed = subprocess.run([sys.executable, "tools/verify_blender_runtime_evidence.py", str(EVIDENCE)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
