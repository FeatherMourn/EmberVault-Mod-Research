"""Reproducible build and loader capability profiles."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .platform_services import GameBuild, GameBuildDetector


@dataclass(frozen=True)
class BuildProfile:
    build: GameBuild
    capabilities: tuple[str, ...]
    schema_files: tuple[str, ...]
    fingerprint: str


class BuildProfileService:
    """Create a stable identity for the game/build/loader evidence set."""

    def snapshot(self, game_dir: Path, capabilities: Iterable[str] = (),
                 schema_root: Path | None = None) -> BuildProfile:
        game_dir = Path(game_dir).resolve()
        build = GameBuildDetector().detect(game_dir)
        capability_names = tuple(sorted({str(value).strip() for value in capabilities if str(value).strip()}))
        schema_files: list[str] = []
        digest = hashlib.sha256()
        digest.update(f"build|{build.build_id or ''}|{build.confidence}\n".encode())
        digest.update(f"source|{build.source or ''}\n".encode())
        for capability in capability_names:
            digest.update(f"capability|{capability}\n".encode())
        if schema_root is not None and Path(schema_root).is_dir():
            root = Path(schema_root).resolve()
            for path in sorted(root.rglob("*.json")):
                if not path.is_file() or path.is_symlink():
                    continue
                relative = path.relative_to(root).as_posix()
                schema_files.append(relative)
                digest.update(f"schema|{relative}|".encode())
                digest.update(hashlib.sha256(path.read_bytes()).digest())
        return BuildProfile(build, capability_names, tuple(schema_files), digest.hexdigest())

    @staticmethod
    def to_dict(profile: BuildProfile) -> dict[str, object]:
        return {
            "schema": "control_center.build_profile.v1",
            "build_id": profile.build.build_id,
            "build_source": profile.build.source,
            "confidence": profile.build.confidence,
            "capabilities": list(profile.capabilities),
            "schema_files": list(profile.schema_files),
            "fingerprint": profile.fingerprint,
        }

    @staticmethod
    def write(profile: BuildProfile, destination: Path) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(BuildProfileService.to_dict(profile), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(destination)
        return destination
