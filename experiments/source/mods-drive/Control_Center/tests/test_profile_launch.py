import json
import tempfile
import unittest
from pathlib import Path

from core.profile_launch import LaunchError, ProfileLaunchService


class ProfileLaunchTests(unittest.TestCase):
    def test_clone_profile_is_independent_and_world_scoped(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.json"
            source.write_text(json.dumps({"id": "base", "config": {"enabled_modules": {"sample": True}}}), encoding="utf-8")
            destination = root / "world-a.json"
            created = ProfileLaunchService().clone_profile(source, destination, "world_a", "world-a")
            data = json.loads(created.read_text(encoding="utf-8"))
            self.assertEqual(data["id"], "world_a")
            self.assertEqual(data["world_id"], "world-a")
            data["config"]["enabled_modules"]["sample"] = False
            self.assertTrue(json.loads(source.read_text(encoding="utf-8"))["config"]["enabled_modules"]["sample"])

    def test_prepare_writes_hashed_runtime_profile(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); game = root / "game"; game.mkdir(); (game / "Enshrouded.exe").write_text("fake", encoding="utf-8")
            profile = root / "profile.json"; profile.write_text(json.dumps({"id": "builder", "config": {"enabled_modules": {"sample": True}}}), encoding="utf-8")
            runtime = root / "runtime" / "launch_profile.json"
            plan = ProfileLaunchService().prepare(game, profile, runtime)
            data = json.loads(runtime.read_text(encoding="utf-8"))
            self.assertEqual(plan.profile_id, "builder")
            self.assertEqual(data["sha256"], plan.profile_hash)
            self.assertEqual(plan.steam_uri, "steam://rungameid/1203620")

    def test_prepare_preserves_world_scope(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); game = root / "game"; game.mkdir(); (game / "Enshrouded.exe").write_text("fake", encoding="utf-8")
            profile = root / "profile.json"; profile.write_text(json.dumps({"id": "world_a", "world_id": "world-a", "config": {"enabled_modules": {}}}), encoding="utf-8")
            runtime = root / "runtime.json"
            ProfileLaunchService().prepare(game, profile, runtime)
            self.assertEqual(json.loads(runtime.read_text(encoding="utf-8"))["world_id"], "world-a")

    def test_prepare_rejects_missing_game(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); game = root / "game"; game.mkdir(); profile = root / "profile.json"; profile.write_text("{}", encoding="utf-8")
            with self.assertRaises(LaunchError): ProfileLaunchService().prepare(game, profile, root / "runtime.json")

    def test_launch_rejects_tampered_runtime_profile(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); game = root / "game"; game.mkdir(); (game / "Enshrouded.exe").write_text("fake", encoding="utf-8")
            profile = root / "profile.json"; profile.write_text(json.dumps({"id": "builder", "config": {"enabled_modules": {}}}), encoding="utf-8")
            runtime = root / "runtime.json"; plan = ProfileLaunchService().prepare(game, profile, runtime)
            runtime.write_text(runtime.read_text(encoding="utf-8").replace('"builder"', '"tampered"'), encoding="utf-8")
            with self.assertRaisesRegex(LaunchError, "hash verification"):
                ProfileLaunchService().launch(plan)

    def test_eml_session_started_requires_log_growth(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "session.eml.log"
            log.write_text("baseline", encoding="utf-8")
            baseline = log.stat().st_size
            self.assertFalse(ProfileLaunchService.eml_session_started(log, baseline))
            log.write_text("baseline\nnew session", encoding="utf-8")
            self.assertTrue(ProfileLaunchService.eml_session_started(log, baseline))


if __name__ == "__main__":
    unittest.main()
