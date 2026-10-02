"""Shared cross-module state used by the Control Center hub."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from .save_backup import list_verified_backups, load_backup_policy


def build_control_context(base_dir: Path, pending: dict[str, Any], installed_mods: dict[str, Any], project: Path | None = None, diagnostics: dict[str, Any] | None = None, *, profile_name: str = "Default") -> dict[str, Any]:
    """Build a read-only summary that pages can share without duplicating policy."""
    base_dir = Path(base_dir).resolve()
    backups = list_verified_backups(base_dir / "profiles" / "save-backups")
    enabled = sum(1 for value in pending.get("enabled_modules", {}).values() if value)
    missing_mods = sum(1 for record in installed_mods.values() if isinstance(record, dict) and not Path(str(record.get("target", ""))).is_dir())
    latest_age_hours = None
    if backups:
        try:
            latest_age_hours = max(0, int((datetime.now(timezone.utc) - datetime.fromtimestamp(Path(backups[0]["path"]).stat().st_mtime, timezone.utc)).total_seconds() // 3600))
        except (OSError, ValueError, TypeError):
            latest_age_hours = None
    return {
        "schema": "control_center.context.v1",
        "profile": {"name": str(profile_name or "Default"), "enabled_module_count": enabled},
        "project": {"path": str(project) if project else None, "name": project.name if project else None},
        "mods": {"installed_count": len(installed_mods), "missing_targets": missing_mods},
        "backups": {"count": sum(1 for item in backups if item["verified"]), "invalid_count": sum(1 for item in backups if not item["verified"]), "latest": backups[0]["name"] if backups else None, "latest_age_hours": latest_age_hours, "policy": load_backup_policy(base_dir / "profiles" / "save-backup-policy.json")},
        "runtime": {"status": str((diagnostics or {}).get("diagnostics", {}).get("status", "unknown"))},
    }
