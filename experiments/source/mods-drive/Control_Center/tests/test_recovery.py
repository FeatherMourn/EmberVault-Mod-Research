import json
import tempfile
import unittest
from pathlib import Path

from core.recovery import ModQuarantineService, RecoveryError


class RecoveryTests(unittest.TestCase):
    def test_quarantine_and_restore_are_reversible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); mods = root / "mods"; mods.mkdir(); mod = mods / "sample_mod"; mod.mkdir()
            (mod / "mod.json").write_text(json.dumps({"id": "sample_mod"}), encoding="utf-8")
            service = ModQuarantineService(root / "state")
            record = service.quarantine(mods, "sample_mod", "loader failure")
            self.assertFalse(mod.exists()); self.assertTrue(record.quarantined.exists())
            restored = service.restore(record.record_path)
            self.assertEqual(restored, mod); self.assertTrue((mod / "mod.json").is_file())

    def test_quarantine_rejects_missing_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); mods = root / "mods"; mods.mkdir(); (mods / "sample_mod").mkdir()
            with self.assertRaises(RecoveryError):
                ModQuarantineService(root / "state").quarantine(mods, "sample_mod", "bad")

    def test_restore_rejects_occupied_original(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); mods = root / "mods"; mods.mkdir(); mod = mods / "sample_mod"; mod.mkdir(); (mod / "mod.json").write_text("{}", encoding="utf-8")
            service = ModQuarantineService(root / "state"); record = service.quarantine(mods, "sample_mod", "bad")
            mod.mkdir();
            with self.assertRaises(RecoveryError): service.restore(record.record_path)

    def test_log_candidates_are_conservative(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "latest.eml.log"
            log.write_text("Module sample_mod failed safely: panic\nnormal mods/ignored text\n", encoding="utf-8")
            self.assertEqual(ModQuarantineService(Path(td) / "state").candidates_from_log(log), ["sample_mod"])


if __name__ == "__main__":
    unittest.main()
