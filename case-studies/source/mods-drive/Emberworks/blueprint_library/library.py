from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from construction_sdk.models import Blueprint


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class BlueprintLibrary:
    """Filesystem-backed catalog with immutable revision files."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.active = self.root / "active"
        self.revisions = self.root / "revisions"
        self.archived = self.root / "archived"
        for directory in (self.active, self.revisions, self.archived):
            directory.mkdir(parents=True, exist_ok=True)

    def validate(self, blueprint: Blueprint) -> ValidationReport:
        errors: list[str] = []
        warnings: list[str] = []
        if not blueprint.name.strip():
            errors.append("name is required")
        seen = set()
        for piece in blueprint.pieces:
            if piece.position in seen:
                errors.append(f"duplicate position: {piece.position}")
            seen.add(piece.position)
            if not piece.resource_id.strip():
                errors.append(f"empty resource at {piece.position}")
            if piece.orientation not in (0, 90, 180, 270):
                errors.append(f"invalid orientation at {piece.position}")
        if not blueprint.pieces:
            warnings.append("blueprint contains no pieces")
        return ValidationReport(not errors, tuple(errors), tuple(warnings))

    def save(self, blueprint: Blueprint) -> Path:
        report = self.validate(blueprint)
        if not report.valid:
            raise ValueError("invalid blueprint: " + "; ".join(report.errors))
        blueprint.blueprint_id = blueprint.blueprint_id or str(uuid.uuid4())
        path = self.active / f"{blueprint.blueprint_id}.json"
        path.write_text(json.dumps(blueprint.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return path

    def save_revision(self, blueprint: Blueprint, revision: int) -> Path:
        """Write an immutable revision without changing the active copy."""
        if revision < 1:
            raise ValueError("revision must be positive")
        report = self.validate(blueprint)
        if not report.valid:
            raise ValueError("invalid blueprint: " + "; ".join(report.errors))
        blueprint.blueprint_id = blueprint.blueprint_id or str(uuid.uuid4())
        directory = self.revisions / blueprint.blueprint_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{revision}.json"
        if path.exists():
            raise FileExistsError(f"revision already exists: {revision}")
        path.write_text(json.dumps(blueprint.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return path

    def load_revision(self, blueprint_id: str, revision: int) -> Blueprint:
        path = self.revisions / blueprint_id / f"{revision}.json"
        if not path.exists():
            raise FileNotFoundError(f"{blueprint_id}@{revision}")
        return Blueprint.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_revisions(self, blueprint_id: str) -> list[int]:
        directory = self.revisions / blueprint_id
        if not directory.exists():
            return []
        return sorted(int(path.stem) for path in directory.glob("*.json") if path.stem.isdigit())

    def load(self, blueprint_id: str) -> Blueprint:
        path = self.active / f"{blueprint_id}.json"
        if not path.exists():
            raise FileNotFoundError(blueprint_id)
        return Blueprint.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def archive(self, blueprint_id: str) -> Path:
        source = self.active / f"{blueprint_id}.json"
        if not source.exists():
            raise FileNotFoundError(blueprint_id)
        target = self.archived / source.name
        source.replace(target)
        return target

    def search(self, query: str = "", tags: set[str] | None = None) -> list[Blueprint]:
        result = []
        query = query.casefold()
        for path in sorted(self.active.glob("*.json")):
            blueprint = Blueprint.from_dict(json.loads(path.read_text(encoding="utf-8")))
            blueprint_tags = set(blueprint.metadata.get("tags", []))
            if query and query not in blueprint.name.casefold() and query not in path.stem.casefold():
                continue
            if tags and not tags.issubset(blueprint_tags):
                continue
            result.append(blueprint)
        return result
