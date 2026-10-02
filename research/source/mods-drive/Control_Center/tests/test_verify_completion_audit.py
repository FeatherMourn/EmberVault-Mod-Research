import json
import tempfile
import unittest
import os
import sys
from unittest.mock import patch
from pathlib import Path

from tools.verify_completion_audit import REQUIRED_DOCS, audit, main


class CompletionAuditTests(unittest.TestCase):
    def test_unresolved_capabilities_prevent_completion_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for path in ["docs/USER_GUIDE.md"]:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("ok", encoding="utf-8")
            capability = root / "capability.json"
            capability.write_text(json.dumps({
                "schema": "control_center.capability_audit.v1",
                "capabilities": [{"id": "x", "state": "research-only"}],
            }), encoding="utf-8")
            result = audit(root, capability)
            self.assertFalse(result["project_complete"])
            self.assertIn("x", result["unresolved_capabilities"])

    def test_unresolved_capability_requires_evidence_and_next_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            capability = root / "capability.json"
            capability.write_text(json.dumps({
                "schema": "control_center.capability_audit.v1",
                "capabilities": [{"id": "x", "state": "research-only"}],
            }), encoding="utf-8")
            result = audit(root, capability)
            self.assertIn("unresolved capability lacks evidence: x", result["errors"])
            self.assertIn("unresolved capability lacks next gate: x", result["errors"])

    def test_missing_evidence_path_fails_audit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            capability = root / "capability.json"
            capability.write_text(json.dumps({
                "schema": "control_center.capability_audit.v1",
                "capabilities": [{"id": "x", "state": "research-only", "evidence": ["missing.json"], "next_gate": "do more research"}],
            }), encoding="utf-8")
            result = audit(root, capability)
            self.assertIn("missing capability evidence: x -> missing.json", result["errors"])

    def test_malformed_capability_audit_is_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            capability = root / "capability.json"
            capability.write_text(json.dumps({"capabilities": [{"id": "x", "state": "guess"}]}), encoding="utf-8")
            result = audit(root, capability)
            self.assertFalse(result["valid"])
            self.assertIn("capability audit schema is unsupported", result["errors"])
            self.assertIn("capability 0 has an invalid state", result["errors"])

    def test_failed_milestone_blocks_audit_validity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            capability = root / "capability.json"
            capability.write_text(json.dumps({
                "schema": "control_center.capability_audit.v1",
                "capabilities": [{"id": "x", "state": "verified"}],
            }), encoding="utf-8")
            result = audit(root, capability, milestone_snapshot={
                "schema": "control_center.milestone_verification.v1", "passed": False,
            })
            self.assertFalse(result["valid"])
            self.assertIn("current milestone verification has failing gates", result["errors"])

    def test_cli_uses_newest_milestone_evidence_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "research").mkdir()
            for relative in REQUIRED_DOCS:
                target = root / relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_text("ok", encoding="utf-8")
            capability = root / "capability.json"
            capability.write_text(json.dumps({"schema": "control_center.capability_audit.v1", "capabilities": [{"id": "x", "state": "verified"}]}), encoding="utf-8")
            older = root / "research" / "MILESTONE_VERIFICATION_old.json"
            newer = root / "research" / "MILESTONE_QUALITY_GATE_new.json"
            older.write_text(json.dumps({"schema": "control_center.milestone_verification.v1", "passed": False}), encoding="utf-8")
            newer.write_text(json.dumps({"schema": "control_center.milestone_verification.v1", "passed": True}), encoding="utf-8")
            os.utime(older, (1, 1)); os.utime(newer, (2, 2))
            with patch.object(sys, "argv", ["verify_completion_audit", "--root", str(root), "--capability-audit", str(capability)]):
                self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
