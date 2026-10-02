import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_ai_sequence_evidence import verify


ROOT = Path(__file__).resolve().parents[1]
SESSIONS = ROOT / "research" / "probe_sessions"
IDENTITY = SESSIONS / "actor_sequence_identity_clone_cycle_20260928"


class AiSequenceEvidenceTests(unittest.TestCase):
    def _verify(self, attachment=None):
        return verify(
            SESSIONS / "actor_sequence_event_graph_cycle_20260928" / "evidence.json",
            IDENTITY / "evidence.json",
            attachment or IDENTITY / "attachment_evidence.json",
            [IDENTITY / "restore.json", IDENTITY / "restore_attachment.json"],
            "1076226",
        )

    def test_current_evidence_chain_passes_without_promotion(self):
        result = self._verify()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["state"], "research-only")
        self.assertFalse(result["promotion_ready"])

    def test_donor_mutation_claim_fails_closed(self):
        path = IDENTITY / "attachment_evidence.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["events"].remove("DONOR_PRESERVED|true")
        with tempfile.TemporaryDirectory() as directory:
            modified = Path(directory) / "attachment.json"
            modified.write_text(json.dumps(data), encoding="utf-8")
            result = self._verify(modified)
        self.assertFalse(result["valid"])
        self.assertTrue(any("DONOR_PRESERVED" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
