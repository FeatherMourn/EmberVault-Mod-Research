import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.crash_recovery import CrashRecoveryService
from core.platform_services import RuntimeHealth


class CrashRecoveryTests(unittest.TestCase):
    def test_running_game_blocks_recovery(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); service = CrashRecoveryService(root / "state")
            with patch.object(service, "_running", return_value=True):
                result = service.recover(root)
            self.assertEqual(result.status, "not_triggered")
            self.assertIn("still running", result.message)

    def test_failed_runtime_with_one_candidate_is_quarantined(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); mods = root / "mods"; mods.mkdir(); mod = mods / "bad_mod"; mod.mkdir()
            (mod / "mod.json").write_text(json.dumps({"id": "bad_mod"}), encoding="utf-8")
            log = root / "logs" / "latest.eml.log"; log.parent.mkdir(); log.write_text("fatal: Module bad_mod failed\n", encoding="utf-8")
            service = CrashRecoveryService(root / "state")
            with patch.object(service, "_running", return_value=False), patch.object(service.health, "inspect", return_value=RuntimeHealth("failed", log)):
                result = service.recover(root)
            self.assertEqual(result.status, "quarantined")
            self.assertFalse(mod.exists())

    def test_ambiguous_failure_requires_review(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); mods = root / "mods"; mods.mkdir()
            for name in ("one", "two"):
                path = mods / name; path.mkdir(); (path / "mod.json").write_text("{}", encoding="utf-8")
            log = root / "latest.eml.log"; log.write_text("fatal: Module one failed\nfatal: Module two failed\n", encoding="utf-8")
            service = CrashRecoveryService(root / "state")
            with patch.object(service, "_running", return_value=False), patch.object(service.health, "inspect", return_value=RuntimeHealth("failed", log)):
                result = service.recover(root)
            self.assertEqual(result.status, "review_required")
            self.assertTrue((mods / "one").exists())

    def test_same_failure_log_is_not_processed_twice(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); mods = root / "mods"; mods.mkdir(); mod = mods / "bad_mod"; mod.mkdir()
            (mod / "mod.json").write_text(json.dumps({"id": "bad_mod"}), encoding="utf-8")
            log = root / "logs" / "latest.eml.log"; log.parent.mkdir(); log.write_text("fatal: Module bad_mod failed\n", encoding="utf-8")
            service = CrashRecoveryService(root / "state")
            with patch.object(service, "_running", return_value=False), patch.object(service.health, "inspect", return_value=RuntimeHealth("failed", log)):
                first = service.recover(root)
                self.assertEqual(first.status, "quarantined")
                first.record.quarantined.rename(mod)
                second = service.recover(root)
            self.assertEqual(second.status, "already_processed")
            self.assertTrue(mod.exists())


if __name__ == "__main__":
    unittest.main()
