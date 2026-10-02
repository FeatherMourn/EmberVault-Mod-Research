import json
import tempfile
import unittest
from pathlib import Path

from core.build_profiles import BuildProfileService


class BuildProfileTests(unittest.TestCase):
    def test_snapshot_fingerprint_changes_with_schema_or_capability(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            game = root / "game"
            game.mkdir()
            (game / "build.txt").write_text("1076226", encoding="utf-8")
            schemas = root / "schemas"
            schemas.mkdir()
            (schemas / "types.json").write_text(json.dumps({"ItemInfo": {"id": "u32"}}), encoding="utf-8")
            service = BuildProfileService()
            first = service.snapshot(game, ["assets.register_resource"], schemas)
            second = service.snapshot(game, ["assets.create_content"], schemas)
            self.assertEqual(first.build.build_id, "1076226")
            self.assertNotEqual(first.fingerprint, second.fingerprint)
            self.assertEqual(first.schema_files, ("types.json",))

    def test_write_profile_is_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            game = root / "game"
            game.mkdir()
            (game / "build.txt").write_text("1076226", encoding="utf-8")
            profile = BuildProfileService().snapshot(game)
            destination = BuildProfileService.write(profile, root / "profile.json")
            data = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(data["schema"], "control_center.build_profile.v1")
            self.assertEqual(data["build_id"], "1076226")


if __name__ == "__main__":
    unittest.main()
