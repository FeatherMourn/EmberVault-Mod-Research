import tempfile
import unittest
from pathlib import Path
from tools.verify_asset_import_boundary import verify

class AssetImportBoundaryTests(unittest.TestCase):
    def test_current_boundary_report_is_explicit(self):
        path = Path(__file__).parents[1] / "research" / "ORIGINAL_ASSET_IMPORT_BOUNDARY_20260928.md"
        self.assertTrue(verify(path)["valid"])

    def test_promotion_rule_requires_runtime_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "boundary.md"
            path.write_text("research-only quarantined File inspection and hashing Dependency and ownership metadata Collision and LOD authoring `TemplateResource` graph access Save persistence and multiplayer authority Promotion rule", encoding="utf-8")
            result = verify(path)
            self.assertFalse(result["valid"])
            self.assertTrue(any("fresh isolated session" in error for error in result["errors"]))

if __name__ == "__main__":
    unittest.main()
