import unittest
from pathlib import Path

from src.rendermodel_inspector import inspect_rendermodel_metadata


class RenderModelInspectorTests(unittest.TestCase):
    def test_inspects_metadata_without_runtime_claims(self):
        fixture = Path(__file__).parent / "fixtures/rendermodel_metadata_v1.json"
        result = inspect_rendermodel_metadata(fixture)
        record = result["records"][0]
        self.assertEqual(result["analysis"]["evidence_type"], "offline-static")
        self.assertEqual(record["metadata"]["vertex_count"], 1200)
        self.assertIn("unverified", record["open_questions"][0])
        self.assertIn("visual substitution", record["unsupported_claims"][0])


if __name__ == "__main__":
    unittest.main()
