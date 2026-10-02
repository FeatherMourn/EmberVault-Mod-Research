"""Fail-closed donor resource patch planning and application.

This layer edits extracted resource JSON only. It produces an auditable patch
plan for later Lua/runtime translation and never modifies a donor in place.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ContentPatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class FieldPatch:
    path: str
    value: Any
    status: str
    reason: str


@dataclass(frozen=True)
class ContentPatchPlan:
    resource_type: str
    donor: Path
    output: Path
    changes: tuple[FieldPatch, ...]
    donor_sha256: str

    @property
    def deployable(self) -> bool:
        return bool(self.changes) and all(change.status == "verified" for change in self.changes)


class ContentPatchPlanner:
    """Create deterministic donor edits with explicit capability gates."""

    VERIFIED_FIELDS = {
        "ItemInfo.name", "ItemInfo.caption", "ItemInfo.description",
        "ItemInfo.iconImage", "ItemInfo.itemId", "RecipeRegistryResource.recipeId",
        "RecipeRegistryResource.debugName", "RecipeRegistryResource.craftTime",
    }
    RESEARCH_FIELDS = {
        "ItemInfo.color", "ItemInfo.materialInteraction", "ItemInfo.iconModel",
        "ItemInfo.iconScene", "RenderModel.materials", "RenderModel.modelMaterialData",
        "RenderModel.meshes", "RenderModel.hierarchy", "ItemInfo.mechanics",
    }

    def plan(self, donor: Path, output: Path, resource_type: str, changes: dict[str, Any]) -> ContentPatchPlan:
        donor = Path(donor); output = Path(output)
        if not donor.is_file():
            raise ContentPatchError(f"Donor resource does not exist: {donor}")
        if donor.resolve() == output.resolve():
            raise ContentPatchError("Patch output must be separate from the donor resource.")
        if not isinstance(changes, dict) or not changes:
            raise ContentPatchError("At least one resource change is required.")
        try:
            donor_bytes = donor.read_bytes()
            donor_sha256 = hashlib.sha256(donor_bytes).hexdigest()
            donor_data = json.loads(donor_bytes.decode("utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise ContentPatchError(f"Unable to read donor resource: {exc}") from exc
        if not isinstance(donor_data, dict):
            raise ContentPatchError("Donor resource must be a JSON object.")
        short = str(resource_type).split("::")[-1]
        patches = []
        for path, value in changes.items():
            key = f"{short}.{path}"
            if key in self.VERIFIED_FIELDS:
                status, reason = "verified", "Supported by the current donor/resource patch contract."
            elif key in self.RESEARCH_FIELDS:
                status, reason = "research-only", "Field is identified but live runtime behavior is not proven."
            else:
                status, reason = "unsupported", "Field is not in the known patch contract."
            existing, present = self._get_path(donor_data, str(path))
            if present and self._kind(existing) != self._kind(value):
                status, reason = "unsupported", f"Value type {self._kind(value)} does not match donor type {self._kind(existing)}."
            elif not present and status == "verified":
                status, reason = "unsupported", "Verified field is absent from this donor resource."
            else:
                semantic_error = self._validate_value(short, str(path), value)
                if semantic_error:
                    status, reason = "unsupported", semantic_error
            patches.append(FieldPatch(str(path), copy.deepcopy(value), status, reason))
        return ContentPatchPlan(str(resource_type), donor, output, tuple(patches), donor_sha256)

    def apply_extracted(self, plan: ContentPatchPlan, *, allow_research: bool = False) -> Path:
        if not plan.changes:
            raise ContentPatchError("Patch plan has no changes.")
        blocked = [change for change in plan.changes
                   if change.status == "unsupported" or (change.status == "research-only" and not allow_research)]
        if blocked:
            fields = ", ".join(change.path for change in blocked)
            raise ContentPatchError(f"Patch contains blocked fields: {fields}")
        try:
            donor_bytes = plan.donor.read_bytes()
            current_sha256 = hashlib.sha256(donor_bytes).hexdigest()
            if current_sha256 != plan.donor_sha256:
                raise ContentPatchError(
                    "Donor resource changed after the patch plan was created; regenerate the plan."
                )
            data = json.loads(donor_bytes.decode("utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise ContentPatchError(f"Unable to read donor resource: {exc}") from exc
        if not isinstance(data, dict):
            raise ContentPatchError("Donor resource must be a JSON object.")
        result = copy.deepcopy(data)
        for change in plan.changes:
            self._set_path(result, change.path, change.value)
        plan.output.parent.mkdir(parents=True, exist_ok=True)
        plan.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return plan.output

    @staticmethod
    def _set_path(data: dict[str, Any], path: str, value: Any) -> None:
        parts = [part for part in str(path).split(".") if part]
        if not parts:
            raise ContentPatchError("Patch path cannot be empty.")
        current: Any = data
        for part in parts[:-1]:
            if not isinstance(current, dict):
                raise ContentPatchError(f"Cannot descend through non-object at {part}.")
            child = current.get(part)
            if child is None:
                child = {}; current[part] = child
            current = child
        if not isinstance(current, dict):
            raise ContentPatchError(f"Cannot assign through non-object at {parts[-1]}.")
        current[parts[-1]] = copy.deepcopy(value)

    @staticmethod
    def _get_path(data: dict[str, Any], path: str) -> tuple[Any, bool]:
        current: Any = data
        for part in [part for part in str(path).split(".") if part]:
            if not isinstance(current, dict) or part not in current:
                return None, False
            current = current[part]
        return current, True

    @staticmethod
    def _kind(value: Any) -> str:
        if value is None: return "null"
        if isinstance(value, bool): return "bool"
        if isinstance(value, int) and not isinstance(value, bool): return "integer"
        if isinstance(value, float): return "number"
        if isinstance(value, str): return "string"
        if isinstance(value, dict): return "object"
        if isinstance(value, list): return "array"
        return type(value).__name__

    @staticmethod
    def _validate_value(resource_type: str, path: str, value: Any) -> str | None:
        """Reject semantically invalid values even when their JSON type matches."""
        field = f"{resource_type}.{path}"
        if field == "ItemInfo.color":
            if not isinstance(value, dict):
                return "Color must be an object with numeric r, g, and b channels."
            required = ("r", "g", "b")
            if any(channel not in value for channel in required):
                return "Color must include r, g, and b channels."
            channels = required + (("a",) if "a" in value else ())
            for channel in channels:
                component = value[channel]
                if (isinstance(component, bool) or
                        not isinstance(component, (int, float)) or
                        component < 0 or component > 1):
                    return "Color channels must be numbers in the normalized 0..1 range."
        if field in {"ItemInfo.itemId", "RecipeRegistryResource.recipeId"}:
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                return "Identity IDs must be positive integers."
        if field in {"ItemInfo.name", "ItemInfo.caption", "ItemInfo.description",
                     "RecipeRegistryResource.debugName"}:
            if not isinstance(value, str) or not value.strip():
                return "Display fields must contain non-empty text."
        if field == "RecipeRegistryResource.craftTime":
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                return "Craft time must be a non-negative number."
        return None
