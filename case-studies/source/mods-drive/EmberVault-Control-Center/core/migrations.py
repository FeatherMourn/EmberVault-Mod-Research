"""Versioned local-data migration and recovery service."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class MigrationItem:
    path: str
    status: str
    records: int = 0
    reason: str = ""


class MigrationService:
    CURRENT_SCHEMA = 1

    def __init__(self, root: Path):
        self.root = Path(root)
        self.backups = self.root / "migration-backups"
        self.quarantine = self.root / "quarantine"

    def _files(self) -> list[Path]:
        return sorted(path for path in self.root.rglob("*.json")
                      if not any(part in {"migration-backups", "quarantine"} for part in path.parts))

    @staticmethod
    def _stamp(payload):
        if isinstance(payload, dict):
            updated = dict(payload)
            updated.setdefault("schema_version", 1)
            return updated, 1
        if isinstance(payload, list):
            updated, changed = [], 0
            for item in payload:
                if not isinstance(item, dict):
                    raise ValueError("Record is not an object")
                record = dict(item); record.setdefault("schema_version", 1)
                changed += int("schema_version" not in item)
                updated.append(record)
            return updated, len(updated)
        raise ValueError("Root JSON value must be an object or array")

    def preview(self) -> list[MigrationItem]:
        items = []
        for path in self._files():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                updated, count = self._stamp(raw)
                status = "ready" if updated != raw else "current"
                items.append(MigrationItem(str(path.relative_to(self.root)), status, count))
            except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
                items.append(MigrationItem(str(path.relative_to(self.root)), "quarantine", reason=str(exc)))
        return items

    def apply(self) -> dict:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = self.backups / timestamp
        report = {"schema_version": 1, "backup": str(backup_root), "items": []}
        for item in self.preview():
            source = self.root / item.path
            if item.status == "quarantine":
                destination = self.quarantine / timestamp / item.path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                report["items"].append({**item.__dict__, "quarantine": str(destination)})
                continue
            backup = backup_root / item.path
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup)
            if item.status == "ready":
                raw = json.loads(source.read_text(encoding="utf-8"))
                updated, _ = self._stamp(raw)
                source.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
            report["items"].append(item.__dict__)
        report_path = backup_root / "migration-report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report

    def rollback(self, backup: Path) -> int:
        backup = Path(backup)
        restored = 0
        for source in backup.rglob("*.json"):
            if source.name == "migration-report.json":
                continue
            destination = self.root / source.relative_to(backup)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            restored += 1
        return restored
