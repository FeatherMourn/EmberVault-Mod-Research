"""Read-only Mod Manager metadata and approval boundary."""
from __future__ import annotations

from typing import Any


def review_mod_manager_request(request: dict[str, Any]) -> dict[str, Any]:
    """Classify a synthetic discovery/update request without executing it."""
    if not isinstance(request, dict):
        raise ValueError("Mod Manager request must be an object.")
    package = request.get("package", {})
    operation = request.get("operation", "discover")
    issues = []
    if not isinstance(package, dict) or not package.get("id"):
        issues.append("package identity is missing")
    if operation not in {"discover", "stage-update", "recovery-review"}:
        issues.append("unsupported operation")
    if operation == "stage-update" and not request.get("backup_id"):
        issues.append("verified backup is required before staging an update")
    if operation == "recovery-review" and not request.get("recovery_evidence"):
        issues.append("recovery evidence is required")
    return {
        "contract_version": 1,
        "operation": operation,
        "state": "blocked" if issues else "review-required",
        "issues": issues,
        "approval_required": operation != "discover",
        "read_only": True,
        "executes_installation": False,
        "control_center_authority": True,
        "save_manager_backup_authority": operation == "stage-update",
    }
