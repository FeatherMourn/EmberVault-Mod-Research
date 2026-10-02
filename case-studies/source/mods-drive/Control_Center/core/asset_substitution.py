"""Research-gated plans for replacing visual resource references."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
import re

from .capability_status import CapabilityStatus


class AssetSubstitutionError(ValueError):
    pass


@dataclass(frozen=True)
class AssetSubstitutionPlan:
    donor_item_id: int
    new_item_id: int
    mechanics_policy: str
    substitutions: tuple[dict[str, str], ...]
    color_adjustments: tuple[dict[str, Any], ...] = ()
    state: str = CapabilityStatus.RESEARCH_ONLY.value


class AssetSubstitutionPlanner:
    """Plan visual substitutions without mutating donor mechanics."""

    VISUAL_FIELDS = {"iconImage", "visualModel", "visualEntity", "placedEntity",
                     "iconModel", "iconScene", "material", "texture"}
    OWNERSHIP = {"external-research", "control-center-owned", "vanilla-donor"}

    @staticmethod
    def metadata_policy(resource_type: str) -> dict[str, Any]:
        research_dir = Path(__file__).resolve().parents[1] / "research"
        candidates = sorted(research_dir.glob("SAFE_METADATA_RESOURCE_TYPES_*.json"), reverse=True)
        path = candidates[0] if candidates else research_dir / "SAFE_METADATA_RESOURCE_TYPES_20260928.json"
        try:
            policy = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            return {"state": "unknown", "resource_type": resource_type}
        aliases = [str(resource_type)]
        if not str(resource_type).startswith("keen::"):
            aliases.append("keen::" + str(resource_type))
        for item in policy.get("quarantined_types", []):
            if item.get("type") in aliases:
                return {"state": "quarantined", "resource_type": resource_type,
                        "policy_type": item.get("type"), "reason": item.get("reason"),
                        "target_build": policy.get("target_build")}
        for item in policy.get("verified_types", []):
            if item.get("type") in aliases:
                return {"state": "verified", "resource_type": resource_type,
                        "policy_type": item.get("type"), "target_build": policy.get("target_build")}
        return {"state": "unverified", "resource_type": resource_type,
                "target_build": policy.get("target_build")}

    def plan(self, donor_item_id: int, new_item_id: int,
             substitutions: list[dict[str, str]] | None = None,
             color_adjustments: list[dict[str, Any]] | None = None,
             preserve_mechanics: bool = True) -> AssetSubstitutionPlan:
        if any(not isinstance(value, int) or value <= 0 for value in
               (donor_item_id, new_item_id)):
            raise AssetSubstitutionError("Item IDs must be positive integers.")
        if donor_item_id == new_item_id:
            raise AssetSubstitutionError("Visual substitution requires a distinct new item ID; donor overwrite is prohibited.")
        if not preserve_mechanics:
            raise AssetSubstitutionError("Mechanics replacement requires a separate authority review.")
        normalized: list[dict[str, str]] = []
        seen_fields: set[str] = set()
        for entry in substitutions or []:
            if not isinstance(entry, dict):
                raise AssetSubstitutionError("Each substitution must be an object.")
            field = str(entry.get("field", ""))
            resource_guid = str(entry.get("resource_guid", ""))
            donor_resource_guid = str(entry.get("donor_resource_guid", "")).strip()
            if field not in self.VISUAL_FIELDS:
                raise AssetSubstitutionError(f"Unsupported visual field: {field}")
            if not resource_guid:
                raise AssetSubstitutionError(f"{field} requires resource_guid.")
            if donor_resource_guid and donor_resource_guid == resource_guid:
                raise AssetSubstitutionError(
                    f"{field} replacement must differ from donor resource_guid; a no-op visual substitution is prohibited."
                )
            if field in seen_fields:
                raise AssetSubstitutionError(f"Duplicate visual field: {field}")
            seen_fields.add(field)
            ownership = str(entry.get("ownership", "external-research"))
            if ownership not in self.OWNERSHIP:
                raise AssetSubstitutionError(f"Unsupported ownership: {ownership}")
            normalized_entry = {
                "field": field,
                "resource_guid": resource_guid,
                "ownership": ownership,
            }
            for optional in ("asset", "resource_type"):
                if entry.get(optional) is not None and str(entry[optional]).strip():
                    normalized_entry[optional] = str(entry[optional]).strip()
            if donor_resource_guid:
                normalized_entry["donor_resource_guid"] = donor_resource_guid
            normalized_entry["metadata_policy"] = self.metadata_policy(normalized_entry.get("resource_type", ""))
            normalized.append(normalized_entry)
        normalized_colors: list[dict[str, Any]] = []
        for adjustment in color_adjustments or []:
            if not isinstance(adjustment, dict):
                raise AssetSubstitutionError("Each color adjustment must be an object.")
            color = str(adjustment.get("color", "")).strip()
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?", color):
                raise AssetSubstitutionError("Color adjustments must use #RRGGBB or #RRGGBBAA.")
            target = str(adjustment.get("target", "material")).strip()
            if not target:
                raise AssetSubstitutionError("Color adjustment target cannot be empty.")
            normalized_colors.append({"target": target, "color": color.upper()})
        return AssetSubstitutionPlan(donor_item_id, new_item_id, "preserve",
                                     tuple(normalized), tuple(normalized_colors))

    @staticmethod
    def manifest_metadata(plan: AssetSubstitutionPlan) -> dict[str, Any]:
        policy_states = [item["metadata_policy"] for item in plan.substitutions]
        return {
            "state": plan.state,
            "donor_item_id": plan.donor_item_id,
            "new_item_id": plan.new_item_id,
            "mechanics_policy": plan.mechanics_policy,
            "substitutions": list(plan.substitutions),
            "color_adjustments": list(plan.color_adjustments),
            "resource_dependencies": sorted({item["resource_guid"] for item in plan.substitutions}),
            "metadata_policy_states": policy_states,
            "policy_review_required": any(item.get("state") != "verified" for item in policy_states),
            "requires_resource_graph_validation": True,
            "promotion_evidence": [
                "runtime_verified",
                "visual_verified",
                "rollback_verified",
            ],
        }

    @staticmethod
    def validate_dependencies(plan: AssetSubstitutionPlan,
                              available_resource_guids: set[str] | None = None) -> list[str]:
        """Return missing-resource diagnostics without claiming engine import success."""
        if available_resource_guids is None:
            return ["Resource graph availability was not supplied; runtime validation is required."]
        available = {str(guid).strip() for guid in available_resource_guids if str(guid).strip()}
        return [
            f"Missing visual resource dependency: {entry['resource_guid']}"
            for entry in plan.substitutions
            if entry["resource_guid"] not in available
        ]

    @staticmethod
    def validate_project_dependencies(plan: AssetSubstitutionPlan, project: Any) -> list[str]:
        """Validate against resource IDs recorded by an asset project."""
        from .asset_service import AssetService
        project_data = AssetService()._load(Path(project).resolve())
        references = {
            str(reference.get("resource_id", "")).strip(): str(reference.get("resource_type", "")).strip()
            for reference in project_data.get("references", [])
            if isinstance(reference, dict) and str(reference.get("resource_id", "")).strip()
        }
        issues = AssetSubstitutionPlanner.validate_dependencies(plan, set(references))
        for entry in plan.substitutions:
            expected = str(entry.get("resource_type", "")).strip()
            actual = references.get(entry["resource_guid"], "")
            if expected and actual and expected != actual:
                issues.append(
                    f"Resource type mismatch for {entry['resource_guid']}: expected {expected}, found {actual}."
                )
        return issues
