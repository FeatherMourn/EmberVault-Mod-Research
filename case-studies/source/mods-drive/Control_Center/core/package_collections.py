"""Local package collections and compatibility cataloging."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .compatibility import build_satisfies
from .package_security import PackageSecurityService


@dataclass(frozen=True)
class CatalogEntry:
    package_id: str
    version: str
    author: str | None
    channel: str
    compatibility: str
    integrity: str
    path: Path


class PackageCollectionService:
    """Catalog local package folders without installing or publishing them."""

    SCHEMA = "control_center.package_collection.v1"

    def scan(self, root: Path, build_id: str | None = None) -> tuple[CatalogEntry, ...]:
        root = Path(root).resolve()
        entries: list[CatalogEntry] = []
        for package in sorted(path for path in root.iterdir() if path.is_dir()) if root.is_dir() else []:
            manifest_path = package / "mod.json"
            if not manifest_path.is_file():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                continue
            constraints = manifest.get("compatible_game_builds", [])
            compatible = build_satisfies(build_id, constraints)
            compatibility = "compatible" if compatible is True else ("incompatible" if compatible is False else "unknown")
            lock = PackageSecurityService().verify(package)
            entries.append(CatalogEntry(str(manifest.get("id", package.name)), str(manifest.get("version", "unknown")),
                                        self._author(manifest), str(manifest.get("channel", "stable")),
                                        compatibility, "verified" if lock.valid else "unverified", package))
        return tuple(entries)

    def write(self, destination: Path, entries: tuple[CatalogEntry, ...]) -> Path:
        payload = {"schema": self.SCHEMA, "entries": [
            {"package_id": entry.package_id, "version": entry.version, "author": entry.author,
             "channel": entry.channel, "compatibility": entry.compatibility,
             "integrity": entry.integrity, "path": str(entry.path)}
            for entry in entries
        ]}
        destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(destination)
        return destination

    @staticmethod
    def _author(manifest: dict[str, Any]) -> str | None:
        value = manifest.get("author", manifest.get("authors"))
        if isinstance(value, list):
            return ", ".join(str(item) for item in value)
        return str(value) if value is not None else None
