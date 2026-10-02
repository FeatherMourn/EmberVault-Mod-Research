import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseManifestTests(unittest.TestCase):
    def test_release_verifier_selects_latest_manifest_by_default(self):
        source = (ROOT / "tools" / "verify_release.py").read_text(encoding="utf-8")
        self.assertIn('glob("RELEASE_MANIFEST_*.json")', source)
        self.assertIn("latest_manifest(root)", source)

    def test_release_builder_derives_version_from_latest_manifest(self):
        source = (ROOT / "tools" / "build_release.ps1").read_text(encoding="utf-8")
        self.assertIn("RELEASE_MANIFEST_*.json", source)
        self.assertIn("ConvertFrom-Json).version", source)

    def test_installer_includes_current_authoring_docs(self):
        script = (ROOT / "packaging" / "EnshroudedModHub.iss").read_text(encoding="utf-8")
        self.assertIn("RECIPE_CUSTOMIZATION_AUTHORING_20260928.md", script)
        self.assertIn("RECIPE_KNOWLEDGE_REQUIREMENT_EVIDENCE_20260928.md", script)

    def test_release_artifacts_match_manifest(self):
        manifest = json.loads(
            (ROOT / "packaging" / "RELEASE_MANIFEST_1.0.2.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["schema"], "control_center.release.v1")
        for artifact in manifest["artifacts"]:
            path = ROOT / artifact["path"]
            self.assertTrue(path.is_file(), artifact["path"])
            self.assertEqual(path.stat().st_size, artifact["size"])
            digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
            self.assertEqual(digest, artifact["sha256"])


if __name__ == "__main__":
    unittest.main()
