"""Validation for clone-only visual-reference research evidence."""
from __future__ import annotations

from typing import Any


class VisualReferenceEvidence:
    """Keep accepted field assignment separate from rendered-object proof."""

    @staticmethod
    def validate_report(report: object) -> tuple[str, ...]:
        if not isinstance(report, dict):
            return ("visual reference report must be an object",)
        issues: list[str] = []
        if report.get("schema") != "control_center.visual_reference_probe_session.v1":
            issues.append("unsupported visual reference report schema")
        for key in ("probe_id", "build", "donor_item_guid", "replacement_render_model_guid"):
            if not isinstance(report.get(key), str) or not report[key].strip():
                issues.append(f"{key} is required")
        if not isinstance(report.get("clone_item_id"), int) or report["clone_item_id"] <= 0:
            issues.append("clone_item_id must be a positive integer")
        if report.get("assignment_accepted") is not True:
            issues.append("assignment_accepted must be true")
        if report.get("donor_preservation_checked") is not True:
            issues.append("donor_preservation_checked must be true")
        if report.get("registry_mutation") is not False:
            issues.append("registry_mutation must be false")
        if report.get("panic_observed") is not False:
            issues.append("panic_observed must be false")
        if report.get("placed_object_render_verified") is True and report.get("visual_evidence") is not True:
            issues.append("placed-object rendering cannot be verified without visual_evidence")
        if report.get("state") not in {"experimental", "verified", "research-only"}:
            issues.append("state must be an explicit capability state")
        return tuple(issues)

    @staticmethod
    def validate_registered_report(report: object) -> tuple[str, ...]:
        """Validate the stronger registration/UI boundary without claiming rendering."""
        if not isinstance(report, dict):
            return ("registered visual report must be an object",)
        issues: list[str] = []
        if report.get("schema") != "control_center.registered_visual_substitution_session.v1":
            issues.append("unsupported registered visual report schema")
        for key in ("probe_id", "build", "replacement_render_model_guid", "placed_entity_reference"):
            if not isinstance(report.get(key), str) or not report[key].strip():
                issues.append(f"{key} is required")
        for key in ("clone_item_id", "clone_recipe_id"):
            if not isinstance(report.get(key), int) or report[key] <= 0:
                issues.append(f"{key} must be a positive integer")
        for key in ("visual_assignment_accepted", "clone_discovered", "item_registered", "recipe_registered", "ui_set_cloned"):
            if report.get(key) is not True:
                issues.append(f"{key} must be true")
        if report.get("panic_observed") is not False:
            issues.append("panic_observed must be false")
        if report.get("placed_object_visual_verified") is True:
            issues.append("placed-object visual verification requires separate visual evidence")
        if report.get("state") not in {"experimental", "research-only"}:
            issues.append("registered visual report must remain experimental or research-only")
        return tuple(issues)

