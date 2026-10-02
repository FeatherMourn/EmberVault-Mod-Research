"""Explicit, non-destructive ownership adoption and restore operations."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


class OwnershipError(RuntimeError):
    pass


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class OwnershipService:
    """Manage ownership metadata without replacing the installed payload."""

    OWNER_FILES = (".emh-owner.json", ".emh-third-party-owner.json")

    def _record_path(self, target: Path) -> Path:
        target = Path(target).resolve()
        for name in self.OWNER_FILES:
            candidate = target / name
            if candidate.is_file():
                return candidate
        raise OwnershipError("No ownership record exists for this mod.")

    def _read(self, target: Path) -> tuple[Path, dict[str, Any]]:
        path = self._record_path(target)
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, TypeError) as exc:
            raise OwnershipError(f"Ownership record is invalid: {exc}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
            raise OwnershipError("Ownership record has no valid file map.")
        return path, data

    def adopt_current(self, target: Path, change_source: str = "user") -> dict[str, Any]:
        """Approve current files by changing metadata only."""
        target = Path(target).resolve()
        path, record = self._read(target)
        previous = dict(record.get("files", {}))
        current: dict[str, str] = {}
        for relative in previous:
            file_path = (target / relative).resolve()
            try:
                file_path.relative_to(target)
            except ValueError as exc:
                raise OwnershipError(f"Unsafe owned path: {relative}") from exc
            if not file_path.is_file() or file_path.is_symlink():
                raise OwnershipError(f"Cannot adopt missing or linked file: {relative}")
            current[str(relative).replace("\\", "/")] = _hash(file_path)
        record["files"] = current
        record["previous_files"] = previous
        record["updated_by"] = "control_center"
        record["change_source"] = str(change_source or "user")
        record["managed"] = True
        record["adopted_at"] = __import__("time").time()
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return {"target": str(target), "files": len(current), "change_source": record["change_source"], "overwrote_payload": False}

    def restore_recorded(self, target: Path) -> dict[str, Any]:
        """Restore the recorded backup payload and refresh its hashes."""
        target = Path(target).resolve()
        path, record = self._read(target)
        backup = Path(str(record.get("backup", ""))).resolve()
        if not backup.is_dir():
            raise OwnershipError("Recorded restore point is missing.")
        restored: dict[str, str] = {}
        for source in backup.rglob("*"):
            if source.is_symlink():
                raise OwnershipError("Restore point contains a symbolic link.")
            if not source.is_file():
                continue
            relative = source.relative_to(backup)
            destination = (target / relative).resolve()
            try:
                destination.relative_to(target)
            except ValueError as exc:
                raise OwnershipError(f"Restore point contains an unsafe path: {relative}") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            restored[str(relative).replace("\\", "/")] = _hash(destination)
        if not restored:
            raise OwnershipError("Recorded restore point contains no files.")
        record["files"] = restored
        record["updated_by"] = "control_center"
        record["change_source"] = "control_center_restore"
        record["restored_from"] = str(backup)
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return {"target": str(target), "files": len(restored), "restore_point": str(backup)}
