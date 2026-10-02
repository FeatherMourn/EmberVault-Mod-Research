"""Reversible mod quarantine and deployment recovery primitives."""
from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path


class RecoveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class QuarantineRecord:
    mod_id: str
    original: Path
    quarantined: Path
    reason: str
    created_at: float
    record_path: Path


class ModQuarantineService:
    """Move only an identified mod directory to a reversible quarantine area."""

    MOD_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir).resolve()
        self.quarantine_dir = self.state_dir / "quarantine"
        self.records_dir = self.state_dir / "quarantine-records"
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.records_dir.mkdir(parents=True, exist_ok=True)

    def quarantine(self, mods_root: Path, mod_id: str, reason: str) -> QuarantineRecord:
        mods_root = Path(mods_root).resolve()
        if not self.MOD_ID_RE.fullmatch(str(mod_id)):
            raise RecoveryError("Invalid mod identifier.")
        source = (mods_root / mod_id).resolve()
        if source.parent != mods_root:
            raise RecoveryError("Only direct child mod directories may be quarantined.")
        if not source.is_dir() or not (source / "mod.json").is_file():
            raise RecoveryError(f"Owned mod directory or mod.json not found: {source}")
        stamp = time.strftime("%Y%m%d-%H%M%S") + f"-{time.time_ns() % 1_000_000:06d}"
        destination = self.quarantine_dir / f"{stamp}_{mod_id}"
        shutil.move(str(source), str(destination))
        record_path = self.records_dir / f"{stamp}_{mod_id}.json"
        record = QuarantineRecord(str(mod_id), source, destination, str(reason).strip() or "unspecified", time.time(), record_path)
        record_path.write_text(json.dumps({
            "mod_id": record.mod_id, "original": str(record.original), "quarantined": str(record.quarantined),
            "reason": record.reason, "created_at": record.created_at,
        }, indent=2), encoding="utf-8")
        return record

    def candidates_from_log(self, log_path: Path) -> list[str]:
        """Extract conservative module IDs from loader error lines."""
        try:
            lines = Path(log_path).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
        found: set[str] = set()
        patterns = (re.compile(r"Module\s+([A-Za-z0-9_.-]+)\s+failed", re.IGNORECASE), re.compile(r"mods[./]([A-Za-z0-9_.-]+)", re.IGNORECASE))
        for line in lines:
            if not any(marker in line.lower() for marker in ("error", "panic", "failed", "fatal")):
                continue
            for pattern in patterns:
                found.update(match.group(1) for match in pattern.finditer(line))
        return sorted(found)

    def restore(self, record_path: Path) -> Path:
        record_path = Path(record_path).resolve()
        if record_path.parent != self.records_dir:
            raise RecoveryError("Quarantine record must belong to this service.")
        try:
            data = json.loads(record_path.read_text(encoding="utf-8"))
            original = Path(data["original"]).resolve(); quarantined = Path(data["quarantined"]).resolve()
        except (OSError, ValueError, KeyError) as exc:
            raise RecoveryError(f"Invalid quarantine record: {exc}") from exc
        if not quarantined.is_dir():
            raise RecoveryError("Quarantined mod directory is missing.")
        if original.exists():
            raise RecoveryError(f"Original mod location is already occupied: {original}")
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(quarantined), str(original))
        record_path.unlink()
        return original

    def records(self) -> list[QuarantineRecord]:
        result = []
        for path in sorted(self.records_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                result.append(QuarantineRecord(str(data["mod_id"]), Path(data["original"]), Path(data["quarantined"]), str(data["reason"]), float(data["created_at"]), path))
            except (OSError, ValueError, KeyError, TypeError):
                continue
        return result
