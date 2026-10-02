import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_post_rollback_stable_launch import verify


VALID = {
    "schema": "control_center.post_rollback_stable_launch_evidence.v1",
    "game_build": "build",
    "fresh_session_observed": True,
    "stable_profile": {"research_only_mods": [], "unclassified_mods": [],
                        "isolation_ready": True, "status": "ready"},
    "runtime": {"stable_mod_loaded": True, "patches_applied": 1,
                 "runtime_loader_attached": True,
                 "panic_or_probe_error_observed": False},
    "game_stopped_after_check": True,
    "rollback_verified": True,
}


class PostRollbackStableLaunchTests(unittest.TestCase):
    def test_valid_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(VALID), encoding="utf-8")
            result = verify(path, "build")
        self.assertTrue(result["valid"])

    def test_dirty_profile_fails(self):
        dirty = json.loads(json.dumps(VALID))
        dirty["stable_profile"]["research_only_mods"] = ["probe"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(dirty), encoding="utf-8")
            result = verify(path, "build")
        self.assertFalse(result["valid"])
        self.assertIn("research-only modules remain", " ".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
