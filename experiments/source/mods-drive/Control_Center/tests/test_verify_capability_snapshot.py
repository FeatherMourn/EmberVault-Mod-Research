import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_capability_snapshot import verify


class CapabilitySnapshotVerificationTests(unittest.TestCase):
    def test_current_snapshot_has_existing_provenance(self):
        root = Path(__file__).parents[1]
        result = verify(root / "research" / "CAPABILITY_SNAPSHOT_20260928.json")
        self.assertTrue(result["valid"], result["errors"])

    def test_missing_provenance_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "snapshot.json"
            path.write_text(json.dumps({"schema": "control_center.capability_snapshot.v1", "capabilities": [], "capability_counts": {}}), encoding="utf-8")
            result = verify(path)
            self.assertFalse(result["valid"])
            self.assertIn("snapshot input provenance is missing", " ".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
