import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from core.save_backup import SaveBackupError, backup_save_directory, compare_save_snapshots, game_is_running, restore_save_backup, load_backup_policy, save_backup_policy, run_scheduled_backup


class SaveBackupTests(unittest.TestCase):
    def test_game_guard_is_callable(self):
        self.assertIsInstance(game_is_running(), bool)

    def test_backup_policy_round_trips_and_normalizes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "policy.json"
            saved = save_backup_policy(path, {"enabled": True, "interval_hours": 12, "retention": 3})
            self.assertEqual(saved["interval_hours"], 12)
            self.assertTrue(load_backup_policy(path)["enabled"])
            self.assertEqual(load_backup_policy(path)["retention"], 3)

    def test_scheduled_backup_respects_disabled_policy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); policy = root / "policy.json"
            save_backup_policy(policy, {"enabled": False})
            result = run_scheduled_backup(root, root / "backups", policy)
            self.assertEqual(result["status"], "disabled")

    def test_scheduled_backup_creates_verified_snapshot_when_due(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "saves"; source.mkdir(); (source / "characters-index").write_text("index", encoding="utf-8")
            policy = root / "policy.json"; save_backup_policy(policy, {"enabled": True, "interval_hours": 1, "retention": 2})
            with patch("core.save_backup.game_is_running", return_value=False):
                result = run_scheduled_backup(source, root / "backups", policy)
            self.assertEqual(result["status"], "created")
            self.assertTrue(result["verified"])

    def test_backup_and_restore_preserve_hash_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "saves"; backups = root / "backups"; restored = root / "restored"
            source.mkdir(); (source / "characters-index").write_text('{"latest": 2}', encoding="utf-8")
            (source / "characters-2").write_bytes(b"KSC1-test")
            result = backup_save_directory(source, backups, "test")
            self.assertTrue(result["verified"])
            restored_result = restore_save_backup(Path(result["backup"]), restored)
            self.assertTrue(restored_result["verified"])
            self.assertEqual((restored / "characters-2").read_bytes(), b"KSC1-test")

    def test_source_inside_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "saves"; source.mkdir()
            with self.assertRaises(SaveBackupError):
                backup_save_directory(source, source / "backups")

    def test_tampered_backup_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "saves"; backups = root / "backups"; source.mkdir()
            (source / "characters").write_bytes(b"original")
            result = backup_save_directory(source, backups)
            backup = Path(result["backup"]); (backup / "characters").write_bytes(b"tampered")
            with self.assertRaises(SaveBackupError):
                restore_save_backup(backup, root / "restored")

    def test_snapshot_diff_reports_added_removed_and_changed_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "saves"; backups = root / "backups"; source.mkdir()
            (source / "characters").write_bytes(b"one")
            (source / "removed").write_bytes(b"gone")
            first = Path(backup_save_directory(source, backups, "before")["backup"])
            (source / "characters").write_bytes(b"two")
            (source / "removed").unlink(); (source / "added").write_bytes(b"new")
            second = Path(backup_save_directory(source, backups, "after")["backup"])
            diff = compare_save_snapshots(first, second)
            self.assertEqual(diff["changed"], ["characters"])
            self.assertEqual(diff["added"], ["added"])
            self.assertEqual(diff["removed"], ["removed"])

    def test_snapshot_diff_rejects_tampered_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source = root / "saves"; backups = root / "backups"; source.mkdir()
            (source / "characters").write_bytes(b"original")
            first = Path(backup_save_directory(source, backups, "before")["backup"])
            (first / "characters").write_bytes(b"tampered")
            with self.assertRaises(SaveBackupError):
                compare_save_snapshots(first, first)


if __name__ == "__main__":
    unittest.main()
