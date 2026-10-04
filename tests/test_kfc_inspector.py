import unittest
from pathlib import Path

from src.kfc_inspector import inspect_kfc_metadata


class KfcInspectorTests(unittest.TestCase):
    def test_inspects_fixture_as_bounded_offline_records(self):
        fixture = Path(__file__).parent / "fixtures/kfc_metadata_v1.json"
        result = inspect_kfc_metadata(fixture)
        self.assertEqual(result["analysis"]["evidence_type"], "offline-static")
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(result["records"][0]["open_questions"], ["iconTexture"])
        self.assertIn("runtime", result["records"][0]["unsupported_claims"][0])

    def test_rejects_unversioned_fixture(self):
        with self.assertRaises(FileNotFoundError):
            inspect_kfc_metadata(Path(__file__).parent / "fixtures/does-not-exist.json")


if __name__ == "__main__":
    unittest.main()
