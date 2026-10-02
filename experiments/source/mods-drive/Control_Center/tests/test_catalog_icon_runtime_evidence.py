import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_catalog_icon_runtime_evidence import validate


class CatalogIconRuntimeEvidenceTests(unittest.TestCase):
    def test_current_evidence_is_durable(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "research" / "probe_sessions" / "catalog_icon_fallback_runtime_evidence_20260928_r2.json"
        self.assertEqual(validate(path, root), [])

    def test_missing_screenshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = {"schema": "control_center.catalog_icon_runtime_evidence.v1", "evidence": {"nonblank_catalog_tile_visible": True, "durable_visual_evidence": {"catalog_tile_screenshot": "missing.png", "catalog_tile_verdict": "nonblank_tile_visible", "placed_object_verdict": "not_verified", "save_persistence_verdict": "not_verified"}}}
            path = root / "evidence.json"
            path.write_text(json.dumps(evidence), encoding="utf-8")
            self.assertTrue(any("screenshot is missing" in error for error in validate(path, root)))


if __name__ == "__main__":
    unittest.main()
