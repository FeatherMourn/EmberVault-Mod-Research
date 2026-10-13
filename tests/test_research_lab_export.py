import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from src.research_lab_export import (create_snapshot_bundle, prune_snapshot_bundles,
                                     recover_snapshot_bundle, verify_snapshot_bundle)


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
            recovered = Path(directory) / "recovered.json"
            result = recover_snapshot_bundle(bundle, recovered)
            self.assertEqual(json.loads(recovered.read_text())["records"][0]["id"], "r1")
            self.assertTrue(result["read_only"])

    def test_bundle_persists_hashed_analyzer_runs(self):
        snapshot = {"schema_version": 1, "read_only": True, "runtime_approval": False, "records": []}
        runs = [{"analyzer_id": "kfc-inspector", "version": "1", "read_only": True}]
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "lab.zip"
            create_snapshot_bundle(snapshot, bundle, analyzer_runs=runs)
            manifest = verify_snapshot_bundle(bundle)
            self.assertEqual(len(manifest["analyzer_runs_sha256"]), 64)
            self.assertEqual(manifest["analyzer_run_summary"]["count"], 1)
            self.assertEqual(manifest["analyzer_run_summary"]["analyzers"], ["kfc-inspector"])
            with zipfile.ZipFile(bundle) as archive:
                self.assertIn("kfc-inspector", archive.read("analyzer-runs.json").decode("utf-8"))
            recovered = Path(directory) / "recovered.json"
            result = recover_snapshot_bundle(bundle, recovered)
            self.assertTrue(Path(result["analyzer_runs_destination"]).is_file())

    def test_bundle_rejects_runtime_approved_snapshot(self):
        with self.assertRaises(ValueError):
            create_snapshot_bundle({"read_only": True, "runtime_approval": True}, Path("ignored.zip"))

    def test_corrupt_bundle_fails_before_overwriting_destination(self):
        snapshot = {"schema_version": 1, "read_only": True, "runtime_approval": False, "records": []}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "lab.zip"
            destination = root / "recovered.json"
            destination.write_text("original", encoding="utf-8")
            create_snapshot_bundle(snapshot, bundle)
            corrupt = root / "corrupt.zip"
            with zipfile.ZipFile(bundle) as source, zipfile.ZipFile(corrupt, "w") as target:
                target.writestr("manifest.json", source.read("manifest.json"))
                target.writestr("snapshot.json", b"tampered")
            with self.assertRaises(ValueError):
                recover_snapshot_bundle(corrupt, destination)
            self.assertEqual(destination.read_text(encoding="utf-8"), "original")

    def test_abandoned_temp_output_does_not_count_as_recovery(self):
        snapshot = {"schema_version": 1, "read_only": True, "runtime_approval": False, "records": []}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "lab.zip"
            create_snapshot_bundle(snapshot, bundle)
            (root / "recovered.json.tmp-abandoned").write_text("incomplete", encoding="utf-8")
            destination = root / "recovered.json"
            recover_snapshot_bundle(bundle, destination)
            self.assertTrue(destination.is_file())
            self.assertFalse(destination.read_text(encoding="utf-8") == "incomplete")

    def test_retention_prunes_only_oldest_bundles(self):
        snapshot = {"schema_version": 1, "read_only": True, "runtime_approval": False, "records": []}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "keep.txt").write_text("untouched", encoding="utf-8")
            for index in range(3):
                create_snapshot_bundle(snapshot, root / f"lab-{index}.zip")
                (root / f"lab-{index}.zip").touch()
            result = prune_snapshot_bundles(root, keep=2)
            self.assertEqual(len(result["removed"]), 1)
            self.assertTrue((root / "keep.txt").is_file())
            self.assertEqual(len(list(root.glob("*.zip"))), 2)


if __name__ == "__main__":
    unittest.main()
