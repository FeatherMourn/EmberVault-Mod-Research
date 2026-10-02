import tempfile
import unittest
from pathlib import Path

from core.update_migration import UpdateMigrationService


class UpdateMigrationTests(unittest.TestCase):
    def test_build_change_is_detected_and_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            game = Path(td) / "game"; game.mkdir(); (game / "build.txt").write_text("1076226", encoding="utf-8")
            service = UpdateMigrationService(Path(td) / "snapshot.json")
            self.assertEqual(service.inspect(game).state, "unrecorded")
            self.assertEqual(service.record(game).state, "recorded")
            self.assertEqual(service.inspect(game).state, "unchanged")
            (game / "build.txt").write_text("1077000", encoding="utf-8")
            self.assertEqual(service.inspect(game).state, "changed")

    def test_records_historical_profiles_per_build(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); snapshot = root / "snapshot.json"; game = root / "game"; game.mkdir()
            (game / "build.txt").write_text("1076226", encoding="utf-8")
            service = UpdateMigrationService(snapshot); service.record(game, "api.v1")
            (game / "build.txt").write_text("1077000", encoding="utf-8")
            service.record(game, "api.v2")
            self.assertEqual(service.compatibility_profile("1076226")["loader_api"], "api.v1")
            self.assertEqual(service.compatibility_profile("1077000")["loader_api"], "api.v2")

    def test_migration_plan_disables_incompatible_modules(self):
        with tempfile.TemporaryDirectory() as td:
            plan = UpdateMigrationService(Path(td) / "snapshot.json").migration_plan({
                "old": {"compatible_game_builds": [">=1070000", "<1075000"]},
                "unknown": {},
            }, "1076226")
            self.assertEqual(plan[0]["action"], "disable")
            self.assertEqual(plan[1]["action"], "keep")

    def test_update_marks_undeclared_modules_for_review(self):
        with tempfile.TemporaryDirectory() as td:
            service = UpdateMigrationService(Path(td) / "snapshot.json")
            plan = service.migration_plan({"undeclared": {}}, "1077000", update_detected=True)
            self.assertEqual(plan[0]["action"], "review")
            self.assertIn("declares no compatibility range", plan[0]["reason"])

    def test_update_disables_research_only_modules(self):
        with tempfile.TemporaryDirectory() as td:
            service = UpdateMigrationService(Path(td) / "snapshot.json")
            plan = service.migration_plan({"probe": {
                "feature_state": "research-only",
                "compatible_game_builds": [">=1070000"],
            }}, "1077000", update_detected=True)
            self.assertEqual(plan[0]["action"], "disable")
            self.assertIn("fresh post-update evidence", plan[0]["reason"])


if __name__ == "__main__":
    unittest.main()
