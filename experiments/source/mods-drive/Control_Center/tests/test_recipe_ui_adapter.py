import unittest

from core.recipe_ui_adapter import RecipeUiAdapter, RecipeUiPlanError


class RecipeUiAdapterTests(unittest.TestCase):
    def test_plan_captures_fixed_array_safe_ui_route(self):
        plan = RecipeUiAdapter().plan(3531872774, 3987654400, 3987654399)
        self.assertEqual(plan.state, "research-only")
        self.assertIn("clone_containing_fixed_size_recipe_set", plan.operations)
        self.assertIn("replace_typed_hashkey32_entry", plan.operations)
        self.assertNotIn("append_to_fixed_size_set_entries", plan.operations)

    def test_rejects_invalid_ids(self):
        with self.assertRaises(RecipeUiPlanError):
            RecipeUiAdapter().plan(0, 1, 2)

    def test_metadata_is_serializable(self):
        plan = RecipeUiAdapter().plan(1, 2, 3)
        metadata = RecipeUiAdapter.manifest_metadata(plan)
        self.assertEqual(metadata["fixed_array_policy"], "clone_set_replace_typed_entry")


if __name__ == "__main__":
    unittest.main()
