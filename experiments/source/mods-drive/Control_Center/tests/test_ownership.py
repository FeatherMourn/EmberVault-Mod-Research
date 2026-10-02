import json
import tempfile
import unittest
from pathlib import Path

from core.ownership import OwnershipService


class OwnershipTests(unittest.TestCase):
    def test_adopt_updates_metadata_without_overwriting_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); target = root / "mod"; target.mkdir(); backup = root / "backup"; backup.mkdir()
            payload = target / "src.lua"; payload.write_text("current", encoding="utf-8")
            old = backup / "src.lua"; old.write_text("old", encoding="utf-8")
            record = {"files": {"src.lua": "old-hash"}, "backup": str(backup)}
            (target / ".emh-third-party-owner.json").write_text(json.dumps(record), encoding="utf-8")
            result = OwnershipService().adopt_current(target)
            self.assertFalse(result["overwrote_payload"])
            self.assertEqual(payload.read_text(encoding="utf-8"), "current")
            data = json.loads((target / ".emh-third-party-owner.json").read_text())
            self.assertEqual(data["change_source"], "user")
            self.assertEqual(data["previous_files"]["src.lua"], "old-hash")

    def test_restore_recorded_restores_payload_and_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); target = root / "mod"; target.mkdir(); backup = root / "backup"; backup.mkdir()
            (target / "src.lua").write_text("changed", encoding="utf-8")
            (backup / "src.lua").write_text("recorded", encoding="utf-8")
            (target / ".emh-owner.json").write_text(json.dumps({"files": {"src.lua": "changed"}, "backup": str(backup)}), encoding="utf-8")
            OwnershipService().restore_recorded(target)
            self.assertEqual((target / "src.lua").read_text(encoding="utf-8"), "recorded")
            data = json.loads((target / ".emh-owner.json").read_text())
            self.assertEqual(data["change_source"], "control_center_restore")

