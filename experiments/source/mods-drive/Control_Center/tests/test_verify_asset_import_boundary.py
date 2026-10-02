import tempfile
import unittest
from pathlib import Path

from tools.verify_asset_import_boundary import verify


class AssetImportBoundaryTests(unittest.TestCase):
    def test_current_boundary_report_is_valid(self):
        root = Path(__file__).resolve().parents[1]
        self.assertTrue(verify(root / "research" / "ORIGINAL_ASSET_IMPORT_BOUNDARY_20260928.md")["valid"])

    def test_incomplete_report_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            report = Path(td) / "report.md"
            report.write_text("research-only", encoding="utf-8")
            self.assertFalse(verify(report)["valid"])


if __name__ == "__main__":
    unittest.main()
