"""Build-update impact analysis for content projects."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .schema_profiles import SchemaChange, SchemaProfileService, SchemaSnapshot


@dataclass(frozen=True)
class MigrationImpact:
    project: Path
    affected_types: tuple[str, ...]
    changes: tuple[SchemaChange, ...]
    action: str


class MigrationAssistant:
    """Analyze update impact; deployment remains an explicit later action."""

    def __init__(self) -> None:
        self.schemas = SchemaProfileService()

    def analyze(self, before: SchemaSnapshot, after: SchemaSnapshot, projects: list[Path]) -> tuple[MigrationImpact, ...]:
        changes = self.schemas.compare(before, after)
        changed_types = {change.resource_type for change in changes}
        impacts: list[MigrationImpact] = []
        for raw_project in projects:
            project = Path(raw_project).resolve()
            manifest = self._load_manifest(project)
            declared_types = set()
            for entry in manifest.get("content", []) if isinstance(manifest, dict) else []:
                if isinstance(entry, dict) and entry.get("resource_type"):
                    declared_types.add(str(entry["resource_type"]).split("::")[-1])
            for value in manifest.get("required_resource_types", []) if isinstance(manifest, dict) else []:
                declared_types.add(str(value).split("::")[-1])
            affected = tuple(sorted(declared_types & changed_types))
            if affected:
                relevant = tuple(change for change in changes if change.resource_type in affected)
                action = "disable_pending_review" if any(change.severity == "error" for change in relevant) else "rerun_probe"
            else:
                relevant = ()
                action = "unchanged"
            impacts.append(MigrationImpact(project, affected, relevant, action))
        return tuple(impacts)

    @staticmethod
    def _load_manifest(project: Path) -> dict:
        for name in ("mod.json", "content.json", "CLONE_MANIFEST.json"):
            path = project / name
            if path.is_file():
                try:
                    data = json.loads(path.read_text(encoding="utf-8-sig"))
                    return data if isinstance(data, dict) else {}
                except (OSError, ValueError):
                    return {}
        return {}
