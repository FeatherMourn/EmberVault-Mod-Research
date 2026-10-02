"""Inspection, verified backup, preview, and safe restore for saves.

The first-release contract is intentionally conservative: this service never
edits save contents and never overwrites a live save without first creating a
verified backup of the current state.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


class SaveManagerError(RuntimeError):
    pass


@dataclass(frozen=True)
class SaveFile:
    relative_path: str
    size: int
    modified_at: str
    sha256: str


@dataclass(frozen=True)
class SaveSnapshot:
    id: str
    source: str
    created_at: str
    files: tuple[SaveFile, ...]
    verified: bool
    label: str = ""


class SaveManagerService:
    """Operate on explicit directories; callers choose live or copied data."""

    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        self.backups_root = self.data_root / "backups"
        self.backups_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _reject_symlink_path(path: Path, label: str) -> None:
        absolute = Path(path).absolute()
        if any(part.is_symlink() for part in (absolute, *absolute.parents)):
            raise SaveManagerError(f"{label} symlink paths are not supported.")

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @classmethod
    def inspect(cls, save_dir: Path) -> tuple[SaveFile, ...]:
        requested = Path(save_dir)
        cls._reject_symlink_path(requested, "Save directory")
        root = requested.resolve()
        if not root.is_dir():
            raise SaveManagerError(f"Save directory does not exist: {root}")
        files: list[SaveFile] = []
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                raise SaveManagerError(f"Save directory contains an unsupported symlink: {path}")
            if not path.is_file():
                continue
            stat = path.stat()
            files.append(SaveFile(
                relative_path=path.relative_to(root).as_posix(),
                size=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                sha256=cls._hash(path),
            ))
        return tuple(files)

    def backup(self, save_dir: Path, label: str = "") -> SaveSnapshot:
        source_path = Path(save_dir)
        self._reject_symlink_path(source_path, "Save directory")
        files = self.inspect(source_path)
        source = source_path.resolve()
        snapshot_id = f"EV-BACKUP-{uuid.uuid4().hex[:8].upper()}"
        staging = Path(tempfile.mkdtemp(prefix=f"{snapshot_id}-", dir=self.backups_root))
        destination = self.backups_root / snapshot_id
        try:
            shutil.copytree(source, staging / "save")
            copied = self.inspect(staging / "save")
            if tuple((f.relative_path, f.sha256) for f in copied) != tuple((f.relative_path, f.sha256) for f in files):
                raise SaveManagerError("Backup verification failed: copied files differ from source.")
            manifest = SaveSnapshot(snapshot_id, str(source), datetime.now(timezone.utc).isoformat(), copied, True, label)
            (staging / "manifest.json").write_text(json.dumps({**asdict(manifest), "files": [asdict(f) for f in copied]}, indent=2) + "\n", encoding="utf-8")
            os.replace(staging, destination)
            return manifest
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise

    def list_backups(self) -> list[SaveSnapshot]:
        result: list[SaveSnapshot] = []
        for manifest_path in sorted(self.backups_root.glob("EV-BACKUP-*/manifest.json")):
            try:
                raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                result.append(SaveSnapshot(
                    raw["id"], raw["source"], raw["created_at"],
                    tuple(SaveFile(**entry) for entry in raw["files"]), bool(raw["verified"]), raw.get("label", ""),
                ))
            except (OSError, ValueError, KeyError, TypeError):
                continue
        return result

    def verify_backup(self, snapshot_id: str) -> bool:
        snapshot = next((item for item in self.list_backups() if item.id == snapshot_id), None)
        if not snapshot:
            raise SaveManagerError(f"Unknown backup: {snapshot_id}")
        save_dir = self.backups_root / snapshot_id / "save"
        actual = self.inspect(save_dir)
        return tuple((f.relative_path, f.sha256) for f in actual) == tuple((f.relative_path, f.sha256) for f in snapshot.files)

    def require_verified_backup(self, snapshot_id: str, *, profile_id: str,
                                context=None) -> SaveSnapshot:
        """Return a checksum-valid backup for a module handoff.

        The save manager does not edit the backup or infer ownership from its
        contents. The caller supplies the active profile and optional
        IntegrationContext; mismatched context is rejected before use.
        """
        if not isinstance(profile_id, str) or not profile_id.strip():
            raise SaveManagerError("A profile is required for a save handoff")
        if context is not None and context.profile_id != profile_id:
            raise SaveManagerError("Save handoff profile does not match integration context")
        snapshot = next((item for item in self.list_backups() if item.id == snapshot_id), None)
        if not snapshot or not snapshot.verified or not self.verify_backup(snapshot_id):
            raise SaveManagerError("Handoff requires an existing checksum-valid backup")
        return snapshot

    def preview_restore(self, snapshot_id: str, destination: Path) -> dict:
        snapshot = next((item for item in self.list_backups() if item.id == snapshot_id), None)
        if not snapshot:
            raise SaveManagerError(f"Unknown backup: {snapshot_id}")
        if not self.verify_backup(snapshot_id):
            raise SaveManagerError("Selected backup failed verification; preview is unavailable.")
        destination_path = Path(destination)
        self._reject_symlink_path(destination_path, "Restore destination")
        target = destination_path.resolve()
        current = self.inspect(target) if target.is_dir() else ()
        source_paths = {item.relative_path for item in snapshot.files}
        current_paths = {item.relative_path for item in current}
        return {
            "backup_id": snapshot.id,
            "destination": str(target),
            "files_to_add_or_replace": sorted(source_paths),
            "files_to_remove": sorted(current_paths - source_paths),
            "requires_current_backup": target.is_dir(),
        }

    def restore(self, snapshot_id: str, destination: Path, *, current_backup: SaveSnapshot | None = None) -> SaveSnapshot | None:
        destination_path = Path(destination)
        self._reject_symlink_path(destination_path, "Restore destination")
        if current_backup is None and destination_path.exists():
            raise SaveManagerError("Restore requires a verified backup of the current destination.")
        snapshot = next((item for item in self.list_backups() if item.id == snapshot_id), None)
        if not snapshot or not self.verify_backup(snapshot_id):
            raise SaveManagerError("Selected backup is missing or failed verification.")
        source = self.backups_root / snapshot_id / "save"
        target = destination_path.resolve()
        staging = Path(tempfile.mkdtemp(prefix="restore-", dir=self.backups_root))
        try:
            shutil.copytree(source, staging / "save")
            if target.exists():
                shutil.rmtree(target)
            os.replace(staging / "save", target)
            shutil.rmtree(staging, ignore_errors=True)
            if tuple((f.relative_path, f.sha256) for f in self.inspect(target)) != tuple((f.relative_path, f.sha256) for f in snapshot.files):
                raise SaveManagerError("Restored save failed post-restore verification.")
            return current_backup
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
