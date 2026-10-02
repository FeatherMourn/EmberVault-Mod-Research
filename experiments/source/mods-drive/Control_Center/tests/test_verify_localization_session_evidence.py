import json, tempfile, unittest
from pathlib import Path
from tools.verify_localization_session_evidence import verify
class LocalizationSessionEvidenceTests(unittest.TestCase):
    def test_fresh_runtime_record_passes(self):
        root=Path(__file__).resolve().parents[1]
        result = verify(root/"research/probe_sessions/localization_fresh_session_evidence_20260928.json", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z")
        self.assertTrue(result["valid"])
        self.assertFalse(result["promotion_ready"])
        self.assertIn("catalog label screenshot/readback", result["evidence_gaps"])
    def test_ui_overclaim_fails(self):
        with tempfile.TemporaryDirectory() as td:
            data={"schema":"control_center.localization_fresh_session_evidence.v1","build":"x","fresh_session_observed":True,"tag_registration":{"ok":True},"localization_registration":{"ok":True},"panic_observed":False,"probe_uninstalled":True,"stable_profile_restored":True,"ui_label_consumption_verified":True}
            path=Path(td)/"e.json"; path.write_text(json.dumps(data)); self.assertFalse(verify(path,"x")["valid"])
