import tempfile
import unittest
import os
from pathlib import Path

from core.save_manager import SaveManagerError, SaveManagerService


class SaveManagerTests(unittest.TestCase):
    def test_backup_verify_preview_and_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            live = root / "live"
            live.mkdir()
            (live / "characters-index").write_text("one")
            (live / "world.dat").write_text("first")
            service = SaveManagerService(root / "state")
            snapshot = service.backup(live, "before test")
            self.assertTrue(service.verify_backup(snapshot.id))
            (live / "world.dat").write_text("changed")
            preview = service.preview_restore(snapshot.id, live)
            self.assertTrue(preview["requires_current_backup"])
            current = service.backup(live, "before restore")
            service.restore(snapshot.id, live, current_backup=current)
            self.assertEqual((live / "world.dat").read_text(), "first")

    def test_restore_requires_current_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            live = root / "live"
            live.mkdir()
            (live / "save.dat").write_text("data")
            service = SaveManagerService(root / "state")
            snapshot = service.backup(live)
            with self.assertRaises(SaveManagerError):
                service.restore(snapshot.id, live)

    def test_preview_rejects_corrupted_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            live = root / "live"
            live.mkdir()
            (live / "save.dat").write_text("data")
            service = SaveManagerService(root / "state")
            snapshot = service.backup(live)
            (root / "state" / "backups" / snapshot.id / "save" / "save.dat").write_text("tampered")
            with self.assertRaisesRegex(SaveManagerError, "failed verification"):
                service.preview_restore(snapshot.id, live)

    def test_inspection_rejects_symlinked_save_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            live = root / "live"
            live.mkdir()
            outside = root / "outside.dat"
            outside.write_text("outside")
            link = live / "linked.dat"
            try:
                os.symlink(outside, link)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation is unavailable")
            with self.assertRaises(SaveManagerError):
                SaveManagerService.inspect(live)

    def test_backup_and_restore_reject_symlinked_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            live = root / "live"
            live.mkdir()
            (live / "save.dat").write_text("data")
            link = root / "live-link"
            try:
                os.symlink(live, link, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation is unavailable")
            service = SaveManagerService(root / "state")
            with self.assertRaises(SaveManagerError):
                service.backup(link)
            snapshot = service.backup(live)
            with self.assertRaises(SaveManagerError):
                service.preview_restore(snapshot.id, link)
            with self.assertRaises(SaveManagerError):
                service.restore(snapshot.id, link, current_backup=snapshot)


if __name__ == "__main__":
    unittest.main()
