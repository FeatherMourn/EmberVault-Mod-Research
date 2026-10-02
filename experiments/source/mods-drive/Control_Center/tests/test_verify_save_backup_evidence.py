import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_save_backup_evidence import verify


class SaveBackupEvidenceTests(unittest.TestCase):
    def test_verified_backup_restore_record_passes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "evidence.json"
            path.write_text(json.dumps({
                "schema": "control_center.save_backup_evidence.v1",
                "game_stopped": True,
                "source": "save-folder",
                "backup": {"verified": True, "file_count": 3, "manifest_hash_verified": True},
                "restore": {"verified": True, "file_count": 3, "destination_is_temporary": True},
                "cleanup": {"temporary_restore_removed": True},
            }), encoding="utf-8")
            self.assertTrue(verify(path)["passed"])

    def test_failed_restore_record_does_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "evidence.json"
            path.write_text(json.dumps({
                "schema": "control_center.save_backup_evidence.v1",
                "game_stopped": True,
                "backup": {"verified": True, "file_count": 3, "manifest_hash_verified": True},
                "restore": {"verified": False, "file_count": 3, "destination_is_temporary": True},
                "cleanup": {"temporary_restore_removed": True},
            }), encoding="utf-8")
            self.assertFalse(verify(path)["passed"])


if __name__ == "__main__":
    unittest.main()
