"""Distribution, update, repair, and uninstall planning with data preservation."""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from .storage import write_json_atomic


@dataclass
class ReleaseManifest:
    version: str
    channel: str
    platform: str
    package_name: str
    sha256: str = ""


class DistributionService:
    channels = {"stable", "beta", "nightly"}
    platforms = {"windows", "linux"}

    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "distribution"
        self.path.mkdir(parents=True, exist_ok=True)

    def check_update(self, current: str, release: dict) -> dict:
        if not isinstance(release, dict) or release.get("channel") not in self.channels or release.get("platform") not in self.platforms:
            raise ValueError("Invalid release manifest")
        available = str(release.get("version", ""))
        newer = self._version_key(available) > self._version_key(current)
        return {"available": newer, "current": current, "release": release,
                "backup_required": newer, "application_state": "review-only"}

    def backup_before_update(self, destination: Path) -> Path:
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        backup = destination / datetime.now(timezone.utc).strftime("backup-%Y%m%dT%H%M%SZ")
        shutil.copytree(self.root, backup, ignore=shutil.ignore_patterns("distribution"))
        return backup

    def repair_plan(self, installed_files: list[Path], expected_hashes: dict[str, str]) -> dict:
        missing, mismatched = [], []
        for path in installed_files:
            key = str(path)
            if not path.is_file():
                missing.append(key)
            elif key in expected_hashes and self._sha256(path) != expected_hashes[key]:
                mismatched.append(key)
        return {"missing": missing, "mismatched": mismatched, "repair_required": bool(missing or mismatched),
                "automatic_repair": False, "application_state": "review-only"}

    def uninstall_plan(self) -> dict:
        preserved = sorted(str(path.relative_to(self.root)) for path in self.root.iterdir()
                           if path.name not in {"distribution"})
        return {"application_state": "review-only", "preserve_data": True,
                "preserved_paths": preserved, "delete_installation_only": True,
                "automatic_delete": False}

    @staticmethod
    def _version_key(version: str) -> tuple:
        return tuple(int(part) if part.isdigit() else 0 for part in version.lstrip("v").split("."))

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with Path(path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
