"""Plan typed recipe and crafting-UI operations from verified donor evidence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capability_status import CapabilityStatus


class RecipeUiPlanError(ValueError):
    pass


@dataclass(frozen=True)
class RecipeUiPlan:
    donor_recipe_id: int
    new_recipe_id: int
    output_item_id: int
    ui_donor_recipe_id: int
    operations: tuple[str, ...]
    state: str = CapabilityStatus.RESEARCH_ONLY.value


class RecipeUiAdapter:
    """Create an auditable plan; runtime Lua remains separately gated."""

    def plan(self, donor_recipe_id: int, new_recipe_id: int, output_item_id: int,
             ui_donor_recipe_id: int | None = None) -> RecipeUiPlan:
        values = (donor_recipe_id, new_recipe_id, output_item_id)
        if any(not isinstance(value, int) or value <= 0 for value in values):
            raise RecipeUiPlanError("Recipe and item IDs must be positive integers.")
        ui_id = ui_donor_recipe_id if ui_donor_recipe_id is not None else donor_recipe_id
        if not isinstance(ui_id, int) or ui_id <= 0:
            raise RecipeUiPlanError("UI donor recipe ID must be a positive integer.")
        return RecipeUiPlan(
            donor_recipe_id, new_recipe_id, output_item_id, ui_id,
            (
                "resolve_recipe_registry_by_data.recipes",
                "deep_copy_donor_recipe",
                "assign_new_recipe_id",
                "remap_output_item_and_item_ref",
                "append_recipe_to_typed_registry",
                "resolve_fb_ui_bundle_by_data.menu",
                "clone_containing_fixed_size_recipe_set",
                "replace_typed_hashkey32_entry",
                "append_cloned_set_to_group_sets",
            ),
        )

    @staticmethod
    def manifest_metadata(plan: RecipeUiPlan) -> dict[str, Any]:
        return {
            "state": plan.state,
            "donor_recipe_id": plan.donor_recipe_id,
            "new_recipe_id": plan.new_recipe_id,
            "output_item_id": plan.output_item_id,
            "ui_donor_recipe_id": plan.ui_donor_recipe_id,
            "fixed_array_policy": "clone_set_replace_typed_entry",
        }
