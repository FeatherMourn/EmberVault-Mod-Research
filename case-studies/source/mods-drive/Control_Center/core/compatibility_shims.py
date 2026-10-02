"""Manifest-level compatibility adapters for older EML module formats."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


LEGACY_CAPABILITY_NAMES = {
    "assets.create_resource": "assets.register_resource",
    "game.assets.create_resource": "assets.register_resource",
    "game.assets.get_resources": "assets.get_resources_by_type",
}


class CompatibilityShimService:
    """Translate known legacy manifest keys without mutating the source."""

    def adapt_manifest(self, manifest: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        adapted = deepcopy(manifest)
        applied: list[str] = []
        if "required_loader_api" not in adapted and "required_api" in adapted:
            adapted["required_loader_api"] = adapted.pop("required_api")
            applied.append("required_api_to_required_loader_api")
        required = adapted.get("required_loader_api")
        if isinstance(required, str):
            mapped = LEGACY_CAPABILITY_NAMES.get(required)
            if mapped:
                adapted["required_loader_api"] = mapped
                applied.append(f"capability:{required}")
        elif isinstance(required, list):
            normalized = []
            for item in required:
                mapped = LEGACY_CAPABILITY_NAMES.get(str(item), str(item))
                normalized.append(mapped)
                if mapped != item:
                    applied.append(f"capability:{item}")
            adapted["required_loader_api"] = normalized
        if applied:
            adapted["compatibility_shims"] = sorted(set(adapted.get("compatibility_shims", []) + applied))
        return adapted, applied
