"""Plan safe recovery when the game or EML build changes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UpdateRecoveryPlan:
    previous_build: str
    current_build: str
    build_changed: bool
    actions: tuple[str, ...]
    compatible_modules: tuple[str, ...]
    quarantined_modules: tuple[str, ...]
    stale_evidence: bool


def plan_update_recovery(previous_build: str, current_build: str,
                         modules: list[dict[str, Any]],
                         research_modules: set[str] | None = None) -> UpdateRecoveryPlan:
    """Create a non-mutating update plan from manifests and observed builds.

    A changed build never restores research-only modules automatically. Stable
    modules are restored only when their declared game-build constraint matches
    the observed build; unknown or absent constraints are quarantined.
    """
    old = str(previous_build).strip()
    current = str(current_build).strip()
    changed = bool(old and current and old != current)
    research = {str(item) for item in (research_modules or set())}
    compatible: list[str] = []
    quarantined: list[str] = []
    for module in modules:
        module_id = str(module.get("id", "")).strip()
        if not module_id:
            continue
        state = str(module.get("feature_state", module.get("state", ""))).strip()
        declared = str(module.get("game_build", module.get("research_build", ""))).strip()
        if module_id in research or state in {"research-only", "experimental", "disabled"}:
            quarantined.append(module_id)
        elif declared and (declared == current or current.startswith(declared + "|")):
            compatible.append(module_id)
        else:
            quarantined.append(module_id)
    actions = (
        "detect_current_build",
        "preserve_stable_profile_backup",
        "quarantine_research_and_unknown_modules",
        "revalidate_resource_schema",
        "invalidate_stale_runtime_evidence",
        "generate_migration_recommendations",
        "restore_compatible_stable_modules",
        "require_fresh_runtime_evidence",
    ) if changed else ("confirm_build_unchanged", "retain_current_profile")
    return UpdateRecoveryPlan(old, current, changed, actions,
                              tuple(sorted(set(compatible))),
                              tuple(sorted(set(quarantined))), changed)


def plan_metadata(plan: UpdateRecoveryPlan) -> dict[str, Any]:
    return {
        "schema": "control_center.update_recovery_plan.v1",
        "previous_build": plan.previous_build,
        "current_build": plan.current_build,
        "build_changed": plan.build_changed,
        "actions": list(plan.actions),
        "compatible_modules": list(plan.compatible_modules),
        "quarantined_modules": list(plan.quarantined_modules),
        "stale_evidence": plan.stale_evidence,
    }
