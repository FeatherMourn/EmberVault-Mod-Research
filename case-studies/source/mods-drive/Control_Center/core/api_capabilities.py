"""Canonical loader capabilities and backwards-compatible API aliases."""
from __future__ import annotations

from dataclasses import dataclass


CAPABILITY_ALIASES: dict[str, tuple[str, ...]] = {
    "assets.register_resource": ("assets.register_resource", "assets.create_resource"),
    "assets.get_resources_by_type": ("assets.get_resources_by_type",),
    "assets.get_all_resources": ("assets.get_all_resources",),
    "assets.create_hashkey32": ("assets.create_hashkey32", "assets.create_resource:keen::HashKey32"),
}


@dataclass(frozen=True)
class CapabilityResult:
    canonical: str
    supported: bool
    matched: str | None


class CapabilityRegistry:
    def resolve(self, canonical: str, available: set[str]) -> CapabilityResult:
        aliases = CAPABILITY_ALIASES.get(canonical, (canonical,))
        matched = next((alias for alias in aliases if alias in available), None)
        return CapabilityResult(canonical, matched is not None, matched)

    def missing(self, required: list[str] | tuple[str, ...], available: set[str]) -> list[str]:
        return [capability for capability in required if not self.resolve(capability, available).supported]

    def normalize(self, available: set[str]) -> set[str]:
        normalized = set(available)
        for canonical, aliases in CAPABILITY_ALIASES.items():
            if any(alias in available for alias in aliases): normalized.add(canonical)
        return normalized
