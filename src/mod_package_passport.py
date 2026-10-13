"""Shared, read-only metadata passport for an Enshrouded mod package."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def validate_passport(passport: dict[str, Any]) -> list[str]:
    required = ("id", "version", "builds", "targets", "files", "dependencies", "evidence")
    issues = [f"missing:{key}" for key in required if key not in passport]
    if not isinstance(passport.get("builds", []), list):
        issues.append("builds must be a list")
    if not isinstance(passport.get("targets", []), list) or not passport.get("targets"):
        issues.append("targets must be a non-empty list")
    if not isinstance(passport.get("files", []), list):
        issues.append("files must be a list")
    for entry in passport.get("files", []) if isinstance(passport.get("files"), list) else []:
        if not isinstance(entry, dict) or not entry.get("path") or not entry.get("sha256"):
            issues.append("each file requires path and sha256")
    if passport.get("read_only") is not True:
        issues.append("passport must be read-only")
    if passport.get("runtime_approval") is not False:
        issues.append("runtime approval must be false")
    return issues


def build_passport_metadata(passport: dict[str, Any]) -> dict[str, Any]:
    """Validate and hash a passport without reading or executing package files."""
    issues = validate_passport(passport)
    canonical = json.dumps(passport, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"passport_version": 1, "state": "blocked" if issues else "review-required", "issues": issues,
            "passport_sha256": hashlib.sha256(canonical).hexdigest(), "read_only": True,
            "executes_package": False, "runtime_approval": False, "publication": "sanitized-review-only"}
