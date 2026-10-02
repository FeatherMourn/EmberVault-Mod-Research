import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_tuning_runtime_evidence import verify


class TuningRuntimeEvidenceTests(unittest.TestCase):
    def test_repository_evidence_is_valid(self):
        root = Path(__file__).parents[1]
        result = verify(root / "research/probe_sessions/balancing_table_scalar_write_safe_20260929_evidence.json", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z")
        self.assertTrue(result["valid"], result)

    def test_mismatched_readback_is_rejected(self):
        payload = {
            "schema": "control_center.balancing_table_scalar_write_runtime_evidence.v1",
            "target_build": "build", "status": "experimental",
            "runtime": {"write_ok": True, "readback_ok": True, "restore_ok": True,
                         "restored_ok": True, "panic": False, "probe_removed": True,
                         "stable_profile_restored": True, "original_value": 1,
                         "test_value": 2, "readback_value": 3, "restored_value": 1},
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "evidence.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = verify(path, "build")
        self.assertFalse(result["valid"])
        self.assertIn("readback value", " ".join(result["errors"]))
