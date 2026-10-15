import unittest
import tempfile
from pathlib import Path

from src.kfc_inspector import inspect_kfc_metadata


class KfcInspectorTests(unittest.TestCase):
    def test_inspects_fixture_as_bounded_offline_records(self):
        fixture = Path(__file__).parent / "fixtures/kfc_metadata_v1.json"
        result = inspect_kfc_metadata(fixture, approved_root=fixture.parent)
        self.assertEqual(result["analysis"]["evidence_type"], "offline-static")
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(result["records"][0]["open_questions"], ["iconTexture"])
        self.assertIn("runtime", result["records"][0]["unsupported_claims"][0])

    def test_rejects_unversioned_fixture(self):
        with self.assertRaises(ValueError):
            inspect_kfc_metadata(Path(__file__).parent / "fixtures/does-not-exist.json", approved_root=Path(__file__).parent)

    def test_rejects_fixture_outside_approved_root(self):
        fixture = Path(__file__).parent / "fixtures/kfc_metadata_v1.json"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                inspect_kfc_metadata(fixture, approved_root=Path(directory))

    def test_accepts_normalized_kfc4_fixture_without_claiming_native_schema(self):
        fixture = Path(__file__).parent / "fixtures/kfc_metadata_v1.json"
        result = inspect_kfc_metadata(fixture, approved_root=fixture.parent, kfc_format="KFC4")
        self.assertEqual(result["analysis"]["analyzer_id"], "kfc4-metadata-inspector")
        self.assertEqual(result["records"][0]["kind"], "kfc4-metadata")
        self.assertIn("native KFC4 schema", result["records"][0]["unsupported_claims"][0])


if __name__ == "__main__":
    unittest.main()
