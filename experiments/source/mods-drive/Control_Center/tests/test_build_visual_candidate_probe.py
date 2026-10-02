import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VisualCandidateProbeTests(unittest.TestCase):
    def test_generates_read_only_probe_manifest(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            candidate = root / "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa_177394c7_0.json"
            candidate.write_text(json.dumps({"materials": [{"material": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}]}))
            output = root / "probe"
            result = subprocess.run(
                [sys.executable, "tools/build_visual_candidate_probe.py", str(candidate), str(output)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            self.assertIn("Dependency count: 2", result.stdout)
            manifest = json.loads((output / "mod.json").read_text())
            self.assertEqual(manifest["feature_state"], "research-only")
            self.assertFalse(manifest["runtime_mutation"])
            expected_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
            self.assertEqual(manifest["candidate_sha256"], expected_hash)
            probe_manifest = json.loads((output / "probe_manifest.json").read_text())
            self.assertEqual(probe_manifest["schema"], "control_center.visual_candidate_probe_manifest.v1")
            self.assertEqual(probe_manifest["candidate_sha256"], expected_hash)
            self.assertTrue((output / "src" / "mod.lua").exists())

    def test_rejects_candidate_without_guid_prefix(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            candidate = root / "not-a-guid_candidate.json"
            candidate.write_text(json.dumps({"materials": []}))
            result = subprocess.run(
                [sys.executable, "tools/build_visual_candidate_probe.py", str(candidate), str(root / "probe")],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("valid resource GUID", result.stderr)

    def test_prefers_embedded_resource_guid_for_descriptive_filename(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            candidate = root / "descriptive_template_variant.json"
            candidate.write_text(json.dumps({"$guid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "materials": []}))
            output = root / "probe"
            subprocess.run(
                [sys.executable, "tools/build_visual_candidate_probe.py", str(candidate), str(output)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            manifest = json.loads((output / "mod.json").read_text())
            self.assertEqual(manifest["dependency_guids"], ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"])


if __name__ == "__main__":
    unittest.main()
