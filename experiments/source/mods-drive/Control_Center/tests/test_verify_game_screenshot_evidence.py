import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_game_screenshot_evidence import verify


class ScreenshotEvidenceVerificationTests(unittest.TestCase):
    def test_valid_report_requires_real_image(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = root / "catalog.png"
            image.write_bytes(b"png")
            report = root / "catalog.json"
            report.write_text(json.dumps({
                "schema": "control_center.game_screenshot.v1",
                "captured_utc": "2026-09-29T23:00:00Z",
                "evidence_kind": "catalog",
                "path": str(image),
            }), encoding="utf-8")
            result = verify(report)
            self.assertTrue(result["valid"])

    def test_invalid_kind_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = root / "capture.png"
            image.write_bytes(b"png")
            report = root / "capture.json"
            report.write_text(json.dumps({
                "schema": "control_center.game_screenshot.v1",
                "captured_utc": "2026-09-29T23:00:00Z",
                "evidence_kind": "visual_proof",
                "path": str(image),
            }), encoding="utf-8")
            result = verify(report)
            self.assertFalse(result["valid"])
            self.assertIn("evidence_kind", " ".join(result["errors"]))

    def test_item_info_and_recipe_are_first_class_kinds(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image = root / "capture.png"
            image.write_bytes(b"png")
            for kind in ("item_info", "recipe"):
                report = root / f"{kind}.json"
                report.write_text(json.dumps({
                    "schema": "control_center.game_screenshot.v1",
                    "captured_utc": "2026-09-29T23:00:00Z",
                    "evidence_kind": kind,
                    "path": str(image),
                }), encoding="utf-8")
                self.assertTrue(verify(report)["valid"], kind)


if __name__ == "__main__":
    unittest.main()
