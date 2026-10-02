import unittest

from core.update_recovery import plan_metadata, plan_update_recovery


class UpdateRecoveryTests(unittest.TestCase):
    def test_changed_build_quarantines_research_and_unknown_modules(self):
        plan = plan_update_recovery(
            "old", "new",
            [{"id": "stable", "feature_state": "stable", "game_build": "new"},
             {"id": "probe", "feature_state": "research-only", "game_build": "old"},
             {"id": "unknown", "feature_state": "stable"}],
        )
        self.assertTrue(plan.build_changed)
        self.assertEqual(plan.compatible_modules, ("stable",))
        self.assertEqual(plan.quarantined_modules, ("probe", "unknown"))
        self.assertIn("invalidate_stale_runtime_evidence", plan.actions)
        self.assertTrue(plan_metadata(plan)["stale_evidence"])

    def test_unchanged_build_retains_profile(self):
        plan = plan_update_recovery("same", "same", [{"id": "x"}])
        self.assertFalse(plan.build_changed)
        self.assertEqual(plan.actions, ("confirm_build_unchanged", "retain_current_profile"))


if __name__ == "__main__":
    unittest.main()
