"""Fixed-array-safe recipe and UI catalog editing primitives."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any


class CatalogEditError(RuntimeError):
    pass


@dataclass(frozen=True)
class CatalogEditResult:
    value: dict[str, Any]
    donor_entry_index: int | None = None
    cloned_set: bool = False


class CatalogEditor:
    """Pure transformations that never mutate the donor catalog in place."""

    @staticmethod
    def clone_recipe(recipe: dict[str, Any], new_recipe_id: int, new_item_id: int) -> dict[str, Any]:
        if not isinstance(recipe, dict):
            raise CatalogEditError("Recipe must be an object.")
        if any(not isinstance(value, int) or value <= 0 for value in (new_recipe_id, new_item_id)):
            raise CatalogEditError("Cloned recipe and output item IDs must be positive integers.")
        if "output" in recipe and not isinstance(recipe.get("output"), list):
            raise CatalogEditError("Recipe output must be a list.")
        cloned = copy.deepcopy(recipe)
        recipe_id = cloned.get("recipeId")
        if isinstance(recipe_id, dict): recipe_id["value"] = new_recipe_id
        else: cloned["recipeId"] = {"value": new_recipe_id}
        for output in cloned.get("output", []) or []:
            if not isinstance(output, dict):
                raise CatalogEditError("Recipe output entries must be objects.")
            item = output.get("item")
            if isinstance(item, dict): item["value"] = new_item_id
            elif item is not None: output["item"] = {"value": new_item_id}
        return cloned

    @staticmethod
    def edit_recipe(recipe: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
        """Return a validated recipe edit without mutating the donor."""
        if not isinstance(recipe, dict) or not isinstance(changes, dict):
            raise CatalogEditError("Recipe and changes must be objects.")
        allowed = {
            "debugName", "craftTime", "craftingDuration", "ingredients", "input",
            "output", "station", "workshopId", "workshopGuid", "requiredProps",
            "knowledgeRequirement", "amount",
        }
        unknown = sorted(set(changes) - allowed)
        if unknown:
            raise CatalogEditError("Unsupported recipe fields: " + ", ".join(unknown))
        edited = copy.deepcopy(recipe)
        for field, value in changes.items():
            if field in {"ingredients", "input", "output", "requiredProps"} and not isinstance(value, list):
                raise CatalogEditError(f"Recipe field {field} must be a list.")
            if field in {"ingredients", "input", "output"}:
                for entry in value:
                    if not isinstance(entry, dict):
                        raise CatalogEditError(f"Recipe {field} entries must be objects.")
                    quantity = entry.get("amount", entry.get("count", entry.get("quantity", 1)))
                    if not isinstance(quantity, (int, float)) or isinstance(quantity, bool) or quantity <= 0:
                        raise CatalogEditError(f"Recipe {field} quantities must be positive numbers.")
            if field == "craftTime":
                try:
                    if float(value) < 0: raise ValueError
                except (TypeError, ValueError) as exc:
                    raise CatalogEditError("Recipe craftTime must be a non-negative number.") from exc
            edited[field] = copy.deepcopy(value)
        return edited

    @staticmethod
    def clone_recipe_set(bundle: dict[str, Any], donor_recipe_id: int, new_recipe_id: int) -> CatalogEditResult:
        if any(not isinstance(value, int) or value <= 0 for value in (donor_recipe_id, new_recipe_id)):
            raise CatalogEditError("Donor and cloned recipe IDs must be positive integers.")
        if donor_recipe_id == new_recipe_id:
            raise CatalogEditError("Cloned recipe ID must differ from the donor recipe ID.")
        result = copy.deepcopy(bundle)
        trees = (((result.get("menu") or {}).get("crafting") or {}).get("recipes") or {}).get("trees") or []
        existing_values = set()
        for tree in trees:
            for group in tree.get("groups", []) or []:
                for recipe_set in group.get("sets", []) or []:
                    for entry in recipe_set.get("entries", []) if isinstance(recipe_set, dict) else []:
                        value = entry.get("value") if isinstance(entry, dict) else entry
                        if isinstance(value, int):
                            existing_values.add(value)
        if new_recipe_id in existing_values:
            raise CatalogEditError(f"Cloned recipe ID already exists in the UI catalog: {new_recipe_id}")
        for tree in trees:
            for group in tree.get("groups", []) or []:
                sets = group.get("sets", []) or []
                for set_index, recipe_set in enumerate(sets):
                    entries = recipe_set.get("entries", []) if isinstance(recipe_set, dict) else []
                    for entry_index, entry in enumerate(entries):
                        value = entry.get("value") if isinstance(entry, dict) else entry
                        if value == donor_recipe_id:
                            cloned_set = copy.deepcopy(recipe_set)
                            cloned_entries = list(cloned_set.get("entries", []))
                            replacement = cloned_entries[entry_index]
                            if isinstance(replacement, dict): replacement["value"] = new_recipe_id
                            else: cloned_entries[entry_index] = {"value": new_recipe_id}
                            cloned_set["entries"] = cloned_entries
                            # The containing set is cloned and appended; the
                            # fixed-size entries array is replaced at a known
                            # position instead of being extended.
                            group["sets"] = list(sets) + [cloned_set]
                            return CatalogEditResult(result, entry_index, True)
        raise CatalogEditError(f"Donor recipe ID was not found in any UI catalog set: {donor_recipe_id}")
