import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_catalog_preview_matrix import validate


class CatalogPreviewMatrixTests(unittest.TestCase):
    def test_reference_matrix_is_valid(self):
        path = Path("research/templates/catalog_preview_probe_matrix.json")
        self.assertEqual(validate(path), [])

    def test_duplicate_candidate_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.json"
            data = json.loads(Path("research/templates/catalog_preview_probe_matrix.json").read_text(encoding="utf-8"))
            data["candidates"][1]["id"] = data["candidates"][0]["id"]
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any("duplicated" in error for error in validate(path)))


if __name__ == "__main__":
    unittest.main()
