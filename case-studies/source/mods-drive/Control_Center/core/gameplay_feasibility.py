"""Research-only feasibility classification for future gameplay systems."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class GameplayArea(StrEnum):
    INTERACTION = "interaction"
    AI = "ai"
    QUEST = "quest"
    ANIMATION = "animation"
    WORLD_GENERATION = "world_generation"
    MULTIPLAYER_AUTHORITY = "multiplayer_authority"


@dataclass(frozen=True)
class FeasibilityAssessment:
    area: GameplayArea
    state: str
    blockers: tuple[str, ...]
    next_probe: str


class GameplayFeasibilityPlanner:
    """Keep ambitious feature requests explicit and conservatively gated."""

    @staticmethod
    def validate_report(report: object) -> tuple[str, ...]:
        if not isinstance(report, dict):
            return ("feasibility report must be an object",)
        issues: list[str] = []
        if report.get("schema") != "control_center.gameplay_feasibility.v1":
            issues.append("unsupported feasibility report schema")
        if report.get("runtime_mutation") is not False:
            issues.append("runtime_mutation must be false")
        assessments = report.get("assessments")
        if not isinstance(assessments, list) or not assessments:
            issues.append("assessments must be a non-empty array")
        probe = report.get("builder_placement_probe")
        if probe is not None:
            if not isinstance(probe, dict) or probe.get("schema") != "control_center.builder_placement_probe.v1":
                issues.append("builder placement probe schema is invalid")
            elif probe.get("runtime_mutation") is not False:
                issues.append("builder placement probe must be read-only")
        interaction = report.get("interaction_probe")
        if interaction is not None:
            if not isinstance(interaction, dict) or interaction.get("schema") != "control_center.interaction_probe.v1":
                issues.append("interaction probe schema is invalid")
            else:
                if interaction.get("runtime_mutation") is not False:
                    issues.append("interaction probe must be read-only")
                if interaction.get("authority") != "unknown":
                    issues.append("interaction probe authority must remain unknown")
                if interaction.get("execution_scope") != "single-player-read-only":
                    issues.append("interaction probe execution scope must be single-player-read-only")
                if interaction.get("save_policy") != "do-not-save-until-explicitly-approved":
                    issues.append("interaction probe save policy is unsafe")
                donor_guid = interaction.get("donor_resource_guid")
                if isinstance(donor_guid, str) and donor_guid.strip().lower() in {"donor-guid", "placeholder", "example"}:
                    issues.append("interaction probe donor_resource_guid cannot be a placeholder")
        return tuple(issues)

    def assess(self, area: GameplayArea) -> FeasibilityAssessment:
        area = GameplayArea(area)
        if area == GameplayArea.INTERACTION:
            return FeasibilityAssessment(area, "research-only",
                ("custom interaction graph construction is unverified",
                 "authority and persistence behavior unknown"),
                "inventory an asset-backed donor and verify single-player readback")
        if area == GameplayArea.MULTIPLAYER_AUTHORITY:
            return FeasibilityAssessment(area, "unsupported",
                ("server authority and replication are not exposed by the verified route",),
                "identify an authoritative network-owned schema before writing a probe")
        return FeasibilityAssessment(area, "research-only",
            ("original graph construction is unverified", "serialization/authority boundary unknown"),
            f"inventory donor schemas for {area.value} and build a read-only probe")

    def all_assessments(self) -> tuple[FeasibilityAssessment, ...]:
        """Return the complete conservative feasibility matrix in stable order."""
        return tuple(self.assess(area) for area in GameplayArea)

    @staticmethod
    def interaction_probe_spec(donor_resource_guid: str, interaction_key: str,
                               expected_effect: str = "") -> dict[str, Any]:
        """Create a read-only probe contract for an existing interaction.

        This deliberately describes observation and readback only. It does not
        imply that a new interaction, persistence path, or network authority
        can be authored through the current EML route.
        """
        guid = str(donor_resource_guid).strip()
        key = str(interaction_key).strip()
        if not guid:
            raise ValueError("donor_resource_guid is required")
        if not key:
            raise ValueError("interaction_key is required")
        return {
            "schema": "control_center.interaction_probe.v1",
            "state": "research-only",
            "donor_resource_guid": guid,
            "interaction_key": key,
            "expected_effect": str(expected_effect).strip(),
            "observations": [
                "interaction resource resolves",
                "interaction appears in donor graph",
                "single-player invocation readback",
                "persistence boundary readback",
            ],
            "runtime_mutation": False,
            "authority": "unknown",
            "execution_scope": "single-player-read-only",
            "save_policy": "do-not-save-until-explicitly-approved",
            "rollback_policy": "restore-probe-and-profile-before-leaving-session",
            "authority_checks": [
                "identify owning resource or ECS component",
                "distinguish client presentation from server state",
                "record persistence and replication separately",
            ],
            "promotion_requirements": [
                "same-build runtime evidence",
                "no donor mutation",
                "persistence behavior recorded",
                "multiplayer authority separately evaluated",
            ],
        }

    @staticmethod
    def builder_placement_spec(item_id: int, plan_name: str = "") -> dict[str, Any]:
        """Describe a read-only placement-assistance study.

        The current route can prepare plans and inspect donor placement data;
        it does not establish client/server authority to place world objects.
        """
        if not isinstance(item_id, int) or isinstance(item_id, bool) or item_id <= 0:
            raise ValueError("item_id must be a positive integer")
        return {
            "schema": "control_center.builder_placement_probe.v1",
            "state": "research-only",
            "item_id": item_id,
            "plan_name": str(plan_name).strip(),
            "observations": [
                "catalog item resolves",
                "placement template and snap metadata resolve",
                "preview transform can be computed offline",
                "world placement authority and persistence are unknown",
            ],
            "runtime_mutation": False,
            "authority": "unknown",
            "promotion_requirements": [
                "same-build placement preview evidence",
                "server/client authority boundary recorded",
                "persistence and rollback verified",
            ],
        }
