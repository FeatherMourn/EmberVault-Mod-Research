import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_quest_prototype_evidence import verify


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research" / "probe_sessions"


class QuestPrototypeEvidenceTests(unittest.TestCase):
    def _verify(self, standalone=None):
        return verify(
            standalone or BASE / "journal_quest_resource_create_cycle_20260928_edit_evidence.json",
            BASE / "journal_registry_identity_clone_cycle_20260928_typed_array_evidence.json",
            BASE / "journal_registry_identity_clone_cycle_20260928_live_attach_evidence.json",
            [
                BASE / "journal_quest_resource_create_cycle_20260928_edit_restore.json",
                BASE / "journal_registry_identity_clone_cycle_20260928_typed_array_restore.json",
                BASE / "journal_registry_identity_clone_cycle_20260928_live_attach_restore.json",
            ],
            "1076226",
        )

    def test_current_evidence_chain_passes(self):
        result = self._verify()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["state"], "research-only")
        self.assertFalse(result["promotion_ready"])

    def test_missing_donor_integrity_fails_closed(self):
        source = json.loads((BASE / "journal_quest_resource_create_cycle_20260928_edit_evidence.json").read_text())
        source["events"].remove("DONOR_IDENTITY_PRESERVED|true")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            result = self._verify(path)
        self.assertFalse(result["valid"])
        self.assertTrue(any("DONOR_IDENTITY_PRESERVED" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
