"""Verified copy/restore support for Enshrouded save directories.

This layer never edits files in place.  It creates a timestamped snapshot,
records hashes for every copied file, and restores only from a selected
snapshot.  The caller should enforce that the game is closed before either
operation.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SaveBackupError(ValueError):
    """Raised when a backup or restore request is unsafe or invalid."""


def load_backup_policy(path: Path) -> dict[str, Any]:
    """Load the user-owned automatic backup policy with safe defaults."""
    default = {"enabled": False, "interval_hours": 24, "retention": 5, "last_run_utc": None}
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            default.update({key: raw[key] for key in default if key in raw})
    except (OSError, ValueError):
        pass
    default["interval_hours"] = max(1, int(default["interval_hours"]))
    default["retention"] = max(1, int(default["retention"]))
    default["enabled"] = bool(default["enabled"])
    return default


def save_backup_policy(path: Path, policy: dict[str, Any]) -> dict[str, Any]:
    """Persist only the supported automatic backup policy fields."""
    normalized = load_backup_policy(path)
    normalized.update({key: policy[key] for key in ("enabled", "interval_hours", "retention", "last_run_utc") if key in policy})
    normalized["interval_hours"] = max(1, int(normalized["interval_hours"]))
    normalized["retention"] = max(1, int(normalized["retention"]))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")
    return normalized


def prune_save_backups(backup_root: Path, retention: int) -> list[str]:
    """Delete only verified snapshot directories beyond the retention count."""
    snapshots = list_verified_backups(backup_root)
    removed: list[str] = []
    for item in snapshots[max(1, int(retention)):]:
        if not item["verified"]:
            continue
        shutil.rmtree(item["path"])
        removed.append(item["path"])
    return removed


def game_is_running() -> bool:
    """Return a fail-safe process check shared by GUI and CLI callers."""
    if sys.platform != "win32":
        return False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq enshrouded.exe"],
            capture_output=True, text=True, check=False, timeout=3,
        )
    except subprocess.TimeoutExpired:
        return True
    return "enshrouded.exe" in result.stdout.lower()


def _safe_directory(path: Path, label: str) -> Path:
    path = Path(path).expanduser().resolve()
    if not path.is_dir():
        raise SaveBackupError(f"{label} is not an existing directory: {path}")
    if any(item.is_symlink() for item in path.rglob("*")):
        raise SaveBackupError(f"{label} contains a symlink and cannot be snapshotted safely")
    return path


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inventory(root: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "control-center-backup.json"):
        result.append({"path": path.relative_to(root).as_posix(), "size": path.stat().st_size, "sha256": _hash_file(path)})
    return result


def _verified_inventory(root: Path) -> list[dict[str, Any]]:
    manifest_path = root / "control-center-backup.json"
    if not manifest_path.is_file():
        raise SaveBackupError("Backup manifest is missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SaveBackupError(f"Backup manifest is invalid: {exc}") from None
    expected = manifest.get("files")
    actual = _inventory(root)
    if not isinstance(expected, list) or actual != expected:
        raise SaveBackupError("Backup integrity verification failed")
    return actual


def backup_save_directory(source: Path, backup_root: Path, label: str = "manual") -> dict[str, Any]:
    """Copy a complete save directory into a new verified snapshot."""
    source = _safe_directory(source, "Save source")
    backup_root = Path(backup_root).expanduser().resolve()
    backup_root.mkdir(parents=True, exist_ok=True)
    if backup_root == source or backup_root.is_relative_to(source):
        raise SaveBackupError("Backup destination cannot be inside the save source")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = backup_root / f"{stamp}-{label}".replace(" ", "_")
    if target.exists():
        raise SaveBackupError(f"Backup target already exists: {target}")
    shutil.copytree(source, target)
    files = _inventory(target)
    manifest = {"schema": "control_center.save_backup.v1", "source": str(source), "created_utc": stamp, "files": files}
    (target / "control-center-backup.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"backup": str(target), "file_count": len(files), "verified": _inventory(target) == files}


def list_verified_backups(backup_root: Path) -> list[dict[str, Any]]:
    """Return newest-first backup status without modifying any snapshot."""
    root = Path(backup_root).expanduser().resolve()
    if not root.is_dir():
        return []
    results: list[dict[str, Any]] = []
    for snapshot in sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True):
        entry: dict[str, Any] = {"path": str(snapshot), "name": snapshot.name, "verified": False, "file_count": 0}
        try:
            files = _verified_inventory(snapshot)
            entry.update({"verified": True, "file_count": len(files)})
        except SaveBackupError as exc:
            entry["error"] = str(exc)
        results.append(entry)
    return results


def restore_save_backup(backup: Path, destination: Path) -> dict[str, Any]:
    """Restore a verified snapshot into a new or existing destination."""
    backup = _safe_directory(backup, "Backup")
    destination = Path(destination).expanduser().resolve()
    if destination == backup or destination.is_relative_to(backup):
        raise SaveBackupError("Restore destination cannot be inside the backup")
    manifest_path = backup / "control-center-backup.json"
    if not manifest_path.is_file():
        raise SaveBackupError("Backup manifest is missing")
    expected = _verified_inventory(backup)
    destination.mkdir(parents=True, exist_ok=True)
    for path in backup.iterdir():
        if path.name == "control-center-backup.json":
            continue
        target = destination / path.name
        if path.is_dir():
            shutil.copytree(path, target, dirs_exist_ok=True)
        else:
            shutil.copy2(path, target)
    return {"destination": str(destination), "file_count": len(expected), "verified": _inventory(destination) == expected}


def compare_save_snapshots(before: Path, after: Path) -> dict[str, Any]:
    """Compare two verified snapshot directories without exposing file contents."""
    before = _safe_directory(before, "Before snapshot")
    after = _safe_directory(after, "After snapshot")
    before_files = {item["path"]: item["sha256"] for item in _verified_inventory(before)}
    after_files = {item["path"]: item["sha256"] for item in _verified_inventory(after)}
    return {
        "schema": "control_center.save_snapshot_diff.v1",
        "added": sorted(set(after_files) - set(before_files)),
        "removed": sorted(set(before_files) - set(after_files)),
        "changed": sorted(path for path in set(before_files) & set(after_files) if before_files[path] != after_files[path]),
    }


def run_scheduled_backup(source: Path, backup_root: Path, policy_path: Path, now: datetime | None = None) -> dict[str, Any]:
    """Execute one policy-controlled backup for GUI or headless schedulers."""
    policy = load_backup_policy(policy_path)
    if not policy["enabled"]:
        return {"status": "disabled"}
    if game_is_running():
        return {"status": "game_running"}
    current = now or datetime.now(timezone.utc)
    last_raw = policy.get("last_run_utc")
    if last_raw:
        try:
            elapsed = (current - datetime.fromisoformat(str(last_raw))).total_seconds()
        except ValueError:
            elapsed = policy["interval_hours"] * 3600
        if elapsed < policy["interval_hours"] * 3600:
            return {"status": "not_due", "next_in_seconds": int(policy["interval_hours"] * 3600 - elapsed)}
    result = backup_save_directory(source, backup_root, "scheduled")
    updated = save_backup_policy(policy_path, {**policy, "last_run_utc": current.isoformat()})
    removed = prune_save_backups(backup_root, updated["retention"])
    return {"status": "created", "backup": result["backup"], "removed": removed, "verified": result["verified"]}
