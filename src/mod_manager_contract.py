"""Read-only Mod Manager metadata and approval boundary."""
from __future__ import annotations

from typing import Any
import hashlib
import json


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


def discover_package_metadata(package: dict[str, Any], installed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Inspect supplied package metadata and produce a non-executing update plan."""
    installed = installed or {}
    required = ("id", "version", "build", "files")
    missing = [key for key in required if key not in package]
    files = package.get("files", [])
    if not isinstance(files, list):
        missing.append("files-list")
        files = []
    digest = hashlib.sha256(json.dumps(package, sort_keys=True).encode("utf-8")).hexdigest()
    same_version = bool(installed) and installed.get("version") == package.get("version")
    state = "blocked" if missing else ("current" if same_version else "update-available")
    return {
        "package_id": package.get("id", ""),
        "version": package.get("version", ""),
        "build": package.get("build", ""),
        "file_count": len(files),
        "metadata_sha256": digest,
        "state": state,
        "missing": missing,
        "update_plan": None if state in {"blocked", "current"} else {"from": installed.get("version"), "to": package.get("version")},
        "read_only": True,
        "executes_installation": False,
        "requires_backup": state == "update-available",
        "recovery_states": ["not-started", "interrupted", "rolled-back", "verified"],
    }


def simulate_update_recovery(discovery: dict[str, Any], failure: str = "interrupted") -> dict[str, Any]:
    """Create synthetic update failure evidence without changing any package."""
    allowed = {"missing-file", "version-mismatch", "interrupted", "rollback-failed"}
    if failure not in allowed:
        raise ValueError("unsupported synthetic failure")
    issues = list(discovery.get("missing", []))
    if failure == "missing-file" and "required-file" not in issues:
        issues.append("required-file")
    if failure == "version-mismatch":
        issues.append("target build or version differs from installed metadata")
    rollback = "blocked" if failure == "rollback-failed" else "planned"
    return {
        "kind": "synthetic-mod-update-recovery",
        "failure": failure,
        "state": "blocked" if failure in {"missing-file", "rollback-failed"} else "review-required",
        "issues": sorted(set(issues)),
        "rollback": rollback,
        "recovery_evidence": {"source": "synthetic-fixture", "mutation_performed": False},
        "read_only": True,
        "executes_installation": False,
        "requires_control_center_approval": True,
    }
