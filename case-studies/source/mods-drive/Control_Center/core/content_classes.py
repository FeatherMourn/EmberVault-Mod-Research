"""Donor-backed content class profiles and fail-closed package checks."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ContentClassProfile:
    name: str
    status: str
    required_resource_types: tuple[str, ...]
    description: str


PROFILES: dict[str, ContentClassProfile] = {
    "furniture_bed": ContentClassProfile(
        "furniture_bed", "verified",
        ("ItemInfo", "ItemRegistryResource", "RecipeRegistryResource",
         "ItemKnowledgeResource", "FbUiBundle"),
        "Runtime-verified cloned furniture recipe using the bed fixture.",
    ),
    "item": ContentClassProfile(
        "item", "research-only", ("ItemInfo", "ItemRegistryResource"),
        "Requires donor-specific validation for knowledge, visuals, and UI links.",
    ),
    "recipe": ContentClassProfile(
        "recipe", "research-only", ("RecipeRegistryResource",),
        "Requires donor-specific validation for outputs, stations, and catalog placement.",
    ),
    "visual_asset": ContentClassProfile(
        "visual_asset", "research-only", ("RenderModel",),
        "File packaging is supported; engine registration is not runtime-proven.",
    ),
}


class ContentClassService:
    """Resolve content classes and validate their extracted resource families."""

    def profile(self, content_class: str) -> ContentClassProfile:
        try:
            return PROFILES[str(content_class).strip().lower()]
        except KeyError as exc:
            raise ValueError(f"Unknown content class: {content_class}") from exc

    def infer(self, manifest: dict) -> ContentClassProfile | None:
        declared = manifest.get("content_class")
        if declared:
            return self.profile(str(declared))
        if str(manifest.get("schema", "")).startswith("control_center.bed_clone_staging"):
            return PROFILES["furniture_bed"]
        return None

    def validate_resource_families(self, profile: ContentClassProfile, resource_types: Iterable[str]) -> list[str]:
        observed = {str(value).split("::")[-1] for value in resource_types}
        return [f"{resource_type} is required for content class {profile.name}."
                for resource_type in profile.required_resource_types if resource_type not in observed]

    def validate_donor_schema(self, profile: ContentClassProfile, metadata: dict) -> list[str]:
        """Validate the identity/linkage contract before a donor is cloned.

        This remains format-neutral: importers can provide metadata from KFC,
        extracted JSON, or a runtime inspection result without coupling the
        validator to one archive layout.
        """
        issues: list[str] = []
        if not metadata.get("guid"):
            issues.append("Donor GUID is required.")
        if profile.name in {"furniture_bed", "item"} and not metadata.get("item_id"):
            issues.append(f"Donor item_id is required for content class {profile.name}.")
        if profile.name in {"furniture_bed", "recipe"} and not metadata.get("recipe_id"):
            issues.append(f"Donor recipe_id is required for content class {profile.name}.")
        if profile.name == "furniture_bed" and not metadata.get("ui_recipe_link"):
            issues.append("Furniture donor must identify a UI recipe link.")
        if metadata.get("item_id") == metadata.get("recipe_id") and metadata.get("item_id"):
            issues.append("Donor item_id and recipe_id must be distinct.")
        return issues

    @staticmethod
    def resource_types(project: Path) -> set[str]:
        return {path.parent.name for path in Path(project).rglob("*.json")
                if path.name not in {"mod.json", "content.json", "CLONE_MANIFEST.json"}}
