import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_release import verify


class ReleaseVerifierTests(unittest.TestCase):
    def _fixture(self, valid_audit: bool) -> tuple[Path, Path]:
        root = Path(tempfile.mkdtemp())
        (root / "dist").mkdir()
        (root / "research").mkdir()
        artifact = root / "dist" / "tool.exe"
        artifact.write_bytes(b"release")
        evidence = root / "evidence.md"
        evidence.write_text("evidence", encoding="utf-8")
        capabilities = []
        for phase in range(1, 7):
            capabilities.append({
                "phase": phase,
                "id": f"phase-{phase}",
                "state": "verified" if valid_audit else "not-a-state",
                "summary": "fixture",
                "evidence": ["evidence.md"],
                "next_gate": "fixture gate",
            })
        audit = root / "research" / "audit.json"
        audit.write_text(json.dumps({
            "schema": "control_center.capability_audit.v1",
            "audit_date": "2026-09-27",
            "target_build": "test",
            "human_report": "evidence.md",
            "status_policy": ["verified", "experimental", "research-only", "unsupported"],
            "capabilities": capabilities,
        }), encoding="utf-8")
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps({
            "version": "test",
            "capability_audit": "research/audit.json",
            "artifacts": [{"path": "dist/tool.exe", "size": artifact.stat().st_size,
                           "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}],
        }), encoding="utf-8")
        return root, manifest

    def test_release_verifier_accepts_valid_capability_audit(self):
        root, manifest = self._fixture(True)
        self.assertEqual(verify(root, manifest), [])

    def test_release_verifier_rejects_invalid_capability_audit(self):
        root, manifest = self._fixture(False)
        errors = verify(root, manifest)
        self.assertTrue(any("capability audit" in error for error in errors))

    def test_release_verifier_rejects_evidence_outside_project(self):
        root, manifest = self._fixture(True)
        audit = root / "research" / "audit.json"
        data = json.loads(audit.read_text(encoding="utf-8"))
        data["human_report"] = "../outside.md"
        audit.write_text(json.dumps(data), encoding="utf-8")
        errors = verify(root, manifest)
        self.assertTrue(any("escapes project" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
