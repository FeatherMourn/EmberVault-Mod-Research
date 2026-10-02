import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_interaction_probe import verify


class InteractionProbeVerifierTests(unittest.TestCase):
    def manifest(self):
        return {
            "schema": "control_center.interaction_donor_probe.v1",
            "id": "probe",
            "target_build": "1076226",
            "resource_type": "keen::CraftingInteraction",
            "donor_guid": "12345678-1234-4123-8123-123456789abc",
            "entrypoint": "src/mod.lua",
            "feature_state": "research-only",
            "runtime_mutation": False,
            "execution_scope": "single-player-read-only",
            "save_policy": "do-not-save-until-explicitly-approved",
            "rollback_policy": "restore-probe-and-profile-before-leaving-session",
            "authority": "unknown", "persistence": "unknown", "replication": "unknown",
            "prohibited_actions": ["alter saved world state"],
            "evidence_outputs": ["runtime.log"],
        }

    def test_safe_manifest_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mod.json"
            path.write_text(json.dumps(self.manifest()), encoding="utf-8")
            self.assertTrue(verify(path)["valid"])

    def test_mutating_or_placeholder_manifest_fails(self):
        data = self.manifest()
        data["runtime_mutation"] = True
        data["donor_guid"] = "REPLACE_WITH_NON_QUARANTINED_DONOR_GUID"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mod.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = verify(path)
            self.assertFalse(result["valid"])
            self.assertGreaterEqual(len(result["errors"]), 2)


if __name__ == "__main__":
    unittest.main()
