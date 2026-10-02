import tempfile
import unittest
import json
import sys
from pathlib import Path
from unittest.mock import patch

from tools.capture_game_screenshot import capture, main


class CaptureGameScreenshotTests(unittest.TestCase):
    def test_capture_reports_written_png(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "screen.png"

            def fake_run(*args, **kwargs):
                output.write_bytes(b"png")
                return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

            with patch("tools.capture_game_screenshot.subprocess.run", side_effect=fake_run):
                result = capture(output)
            self.assertEqual(result["schema"], "control_center.game_screenshot.v1")
            self.assertEqual(result["capture_mode"], "game_window_or_primary_screen")
            self.assertEqual(result["size"], 3)

    def test_cli_persists_matching_json_report(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "placed_item.png"
            report = Path(td) / "placed_item.json"

            def fake_run(*args, **kwargs):
                output.write_bytes(b"png")
                return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

            with patch("tools.capture_game_screenshot.subprocess.run", side_effect=fake_run), patch.object(
                sys, "argv", ["capture_game_screenshot", str(output), "--report", str(report)]
            ):
                self.assertEqual(main(), 0)
            saved = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(saved["path"], str(output.resolve()))
            self.assertEqual(saved["size"], 3)

    def test_cli_records_evidence_kind(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "catalog.png"
            report = Path(td) / "catalog.json"

            def fake_run(*args, **kwargs):
                output.write_bytes(b"png")
                return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

            with patch("tools.capture_game_screenshot.subprocess.run", side_effect=fake_run), patch.object(
                sys, "argv", ["capture_game_screenshot", str(output), "--report", str(report), "--evidence-kind", "catalog"]
            ):
                self.assertEqual(main(), 0)
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["evidence_kind"], "catalog")


if __name__ == "__main__":
    unittest.main()
