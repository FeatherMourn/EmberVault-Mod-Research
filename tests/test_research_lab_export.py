import json
import tempfile
import unittest
from pathlib import Path

from src.research_lab_export import create_snapshot_bundle, verify_snapshot_bundle


class ResearchLabExportTests(unittest.TestCase):
    def test_bundle_is_hash_verified_and_recoverable(self):
        snapshot = {"schema_version": 1, "read_only": True, "runtime_approval": False,
                    "records": [{"id": "r1"}]}
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "lab.zip"
            create_snapshot_bundle(snapshot, bundle)
            manifest = verify_snapshot_bundle(bundle)
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["recovery"], "verify-before-extract")

    def test_bundle_rejects_runtime_approved_snapshot(self):
        with self.assertRaises(ValueError):
            create_snapshot_bundle({"read_only": True, "runtime_approval": True}, Path("ignored.zip"))


if __name__ == "__main__":
    unittest.main()
