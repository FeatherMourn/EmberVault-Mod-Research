"""Conservative compatibility states and evaluations."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CompatibilityState(StrEnum):
    COMPATIBLE = "compatible"
    WARNINGS = "compatible-with-warnings"
    UNKNOWN = "unknown"
    INCOMPATIBLE = "incompatible"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Compatibility:
    state: CompatibilityState
    reasons: tuple[str, ...] = ()


def evaluate(*, required_builds: list[str] | None, detected_build: str | None,
             blocked: bool = False, warnings: list[str] | None = None) -> Compatibility:
    if blocked:
        return Compatibility(CompatibilityState.BLOCKED, ("Capability is blocked by policy.",))
    detected = detected_build.strip() if isinstance(detected_build, str) else ""
    builds = [item.strip() for item in (required_builds or []) if isinstance(item, str) and item.strip()]
    if not detected or not builds:
        return Compatibility(CompatibilityState.UNKNOWN, ("Build evidence is incomplete.",))
    if detected not in builds:
        return Compatibility(CompatibilityState.INCOMPATIBLE, (f"Build {detected} is not in the tested set.",))
    normalized_warnings = tuple(item.strip() for item in (warnings or []) if isinstance(item, str) and item.strip())
    if normalized_warnings:
        return Compatibility(CompatibilityState.WARNINGS, normalized_warnings)
    return Compatibility(CompatibilityState.COMPATIBLE)
