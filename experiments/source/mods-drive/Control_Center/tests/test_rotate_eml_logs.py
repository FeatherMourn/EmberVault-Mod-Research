import tempfile
import unittest
from pathlib import Path

from unittest.mock import patch

from tools.rotate_eml_logs import apply_rotation, plan


class RotateEmlLogsTests(unittest.TestCase):
    def test_plan_is_dry_and_filters_threshold(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "logs").mkdir()
            (root / "logs" / "small.eml.log").write_bytes(b"x")
            (root / "logs" / "large.eml.log").write_bytes(b"x" * 8)
            result = plan(root, root / "archive", threshold=8)
            self.assertEqual([item["name"] for item in result["candidates"]], ["large.eml.log"])
            self.assertTrue((root / "logs" / "large.eml.log").exists())

    def test_apply_archives_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "logs").mkdir()
            log = root / "logs" / "large.eml.log"; log.write_bytes(b"large")
            with patch("tools.rotate_eml_logs.game_is_running", return_value=False):
                result = apply_rotation(plan(root, root / "archive", threshold=1))
            destination = Path(result["moved"][0]["destination"])
            self.assertFalse(log.exists())
            self.assertEqual(destination.read_bytes(), b"large")
            self.assertTrue((destination.parent / "rotation_manifest.json").exists())

    def test_apply_refuses_when_game_is_running(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "logs").mkdir()
            (root / "logs" / "large.eml.log").write_bytes(b"large")
            with patch("tools.rotate_eml_logs.game_is_running", return_value=True):
                with self.assertRaisesRegex(RuntimeError, "close the game"):
                    apply_rotation(plan(root, root / "archive", threshold=1))


if __name__ == "__main__":
    unittest.main()
