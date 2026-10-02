import json
import tempfile
import unittest
from pathlib import Path

from core.migrations import MigrationService


class MigrationTests(unittest.TestCase):
    def test_preview_apply_and_rollback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "profiles" / "default.json"
            path.parent.mkdir(); path.write_text(json.dumps({"id": "default", "name": "Default"}))
            service = MigrationService(root)
            self.assertEqual(service.preview()[0].status, "ready")
            report = service.apply()
            self.assertEqual(json.loads(path.read_text())["schema_version"], 1)
            restored = service.rollback(Path(report["backup"]))
            self.assertEqual(restored, 1)
            self.assertNotIn("schema_version", json.loads(path.read_text()))

    def test_corrupt_record_is_quarantined(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); path = root / "research.json"; path.write_text("{")
            report = MigrationService(root).apply()
            self.assertEqual(report["items"][0]["status"], "quarantine")
            self.assertTrue((root / "quarantine").exists())


if __name__ == "__main__":
    unittest.main()
