import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_catalog_preview_runtime_evidence import validate


class CatalogPreviewRuntimeEvidenceTests(unittest.TestCase):
    def test_partial_runtime_evidence_is_valid(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("runtime_menu.png", "runtime_post_click.png", "runtime_world.png"):
                (root / name).write_bytes(b"png")
            evidence = {"schema": "control_center.catalog_preview_runtime_evidence.v1", "feature_state": "research-only", "eml": {"api_version": "1.3", "probe_loaded": True, "probe_completed_without_panic": True, "ui_links": 1}, "game": {"launched": True, "main_menu_screenshot": "runtime_menu.png", "play_selection_screenshot": "runtime_post_click.png", "world_entry_screenshot": "runtime_world.png"}, "verdict": "partial_runtime_success", "cleanup": {"game_stopped": True, "probe_uninstalled": True, "stable_profile_restored": True}}
            path = root / "evidence.json"
            path.write_text(json.dumps(evidence), encoding="utf-8")
            self.assertEqual(validate(path, root), [])

    def test_panic_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "evidence.json"
            path.write_text(json.dumps({"schema": "control_center.catalog_preview_runtime_evidence.v1", "feature_state": "research-only", "eml": {"api_version": "1.3", "probe_loaded": True, "probe_completed_without_panic": False, "ui_links": 0}}), encoding="utf-8")
            self.assertTrue(any("panic" in error for error in validate(path, root)))


if __name__ == "__main__":
    unittest.main()
