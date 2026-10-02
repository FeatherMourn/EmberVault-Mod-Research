import json, tempfile, unittest
from pathlib import Path
from tools.verify_visual_substitution_session import verify
class VisualSubstitutionSessionTests(unittest.TestCase):
    def test_fresh_record_passes(self):
        root=Path(__file__).resolve().parents[1]; result=verify(root/"research/probe_sessions/registered_visual_substitution_fresh_evidence_20260928.json", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z")
        self.assertTrue(result["valid"])
        self.assertFalse(result["promotion_ready"])
        self.assertIn("human-visible placed-object replacement screenshot", result["evidence_gaps"])
    def test_panic_fails(self):
        with tempfile.TemporaryDirectory() as td:
            data={"schema":"control_center.registered_visual_substitution_fresh_evidence.v1","build":"x","fresh_session_observed":True,"visual_assignment":{"ok":True},"item_registered":True,"recipe_registered":True,"panic_observed":True,"probe_uninstalled":True,"stable_profile_restored":True,"limitations":["not verified"]}
            path=Path(td)/"e.json"; path.write_text(json.dumps(data)); self.assertFalse(verify(path,"x")["valid"])

    def test_verified_record_requires_durable_screenshots(self):
        root=Path(__file__).resolve().parents[1]
        result=verify(root/"research/probe_sessions/registered_visual_substitution_manual_session_20260928.json", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z")
        self.assertTrue(result["valid"])
        self.assertTrue(result["promotion_ready"])

    def test_assignment_only_record_is_valid_but_not_promotable(self):
        with tempfile.TemporaryDirectory() as td:
            data={"schema":"control_center.registered_visual_substitution_fresh_evidence.v1","build":"x","fresh_session_observed":True,"visual_assignment":{"ok":True},"item_registered":False,"recipe_registered":False,"panic_observed":False,"probe_uninstalled":True,"stable_profile_restored":True,"limitations":["visual rendering not verified"],"evidence_scope":"assignment_only","assignment_boundary":"runtime assignment only"}
            path=Path(td)/"e.json"; path.write_text(json.dumps(data)); result=verify(path,"x")
            self.assertTrue(result["valid"])
            self.assertFalse(result["promotion_ready"])

    def test_world_reached_requires_durable_world_evidence(self):
        root=Path(__file__).resolve().parents[1]
        result=verify(root/"research/probe_sessions/visual_substitution_live_20260929_runtime_evidence.json", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z")
        self.assertTrue(result["valid"])

    def test_short_numeric_build_matches_full_eml_build(self):
        root=Path(__file__).resolve().parents[1]
        result=verify(root/"research/probe_sessions/visual_substitution_live_20260929_runtime_evidence.json", "1076226")
        self.assertTrue(result["valid"])

    def test_world_reached_without_screenshot_fails(self):
        with tempfile.TemporaryDirectory() as td:
            data={"schema":"control_center.registered_visual_substitution_fresh_evidence.v1","build":"x","fresh_session_observed":True,"visual_assignment":{"ok":True},"item_registered":True,"recipe_registered":True,"panic_observed":False,"probe_uninstalled":True,"stable_profile_restored":True,"limitations":["visual not verified"],"world_reached":True}
            path=Path(td)/"e.json"; path.write_text(json.dumps(data)); self.assertFalse(verify(path,"x")["valid"])
