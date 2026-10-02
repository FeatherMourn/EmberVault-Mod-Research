"""Cross-build KFC schema snapshots and conservative diffs."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .resource_inspector import ResourceInspector


@dataclass(frozen=True)
class SchemaChange:
    severity: str
    resource_type: str
    path: str
    message: str


@dataclass(frozen=True)
class SchemaSnapshot:
    build_id: str | None
    root: Path
    resources: dict[str, dict[str, Any]]
    fingerprint: str


class SchemaProfileService:
    """Read extracted JSON resources and compare their observed structures."""

    def snapshot(self, root: Path, build_id: str | None = None) -> SchemaSnapshot:
        root = Path(root).resolve()
        resources: dict[str, dict[str, Any]] = {}
        inspector = ResourceInspector()
        for record in inspector.scan(root):
            key = f"{record.resource_type}|{record.path.relative_to(root).as_posix()}"
            resources[key] = {
                "resource_type": record.resource_type,
                "path": record.path.relative_to(root).as_posix(),
                "guid": record.guid,
                "schema": dict(sorted(record.schema.items())),
                "arrays": dict(sorted(record.arrays.items())),
                "sha256": record.sha256,
            }
        fingerprint = self._fingerprint(build_id, resources)
        return SchemaSnapshot(str(build_id) if build_id else None, root, resources, fingerprint)

    def compare(self, before: SchemaSnapshot, after: SchemaSnapshot) -> tuple[SchemaChange, ...]:
        changes: list[SchemaChange] = []
        before_types = {entry["resource_type"] for entry in before.resources.values()}
        after_types = {entry["resource_type"] for entry in after.resources.values()}
        for resource_type in sorted(after_types - before_types):
            changes.append(SchemaChange("warning", resource_type, "", "Resource type appeared in the newer snapshot."))
        for resource_type in sorted(before_types - after_types):
            changes.append(SchemaChange("error", resource_type, "", "Resource type disappeared from the newer snapshot."))
        before_by_type = self._merge_by_type(before.resources)
        after_by_type = self._merge_by_type(after.resources)
        for resource_type in sorted(before_types & after_types):
            old = before_by_type[resource_type]
            new = after_by_type[resource_type]
            for path, kind in old["schema"].items():
                if path not in new["schema"]:
                    changes.append(SchemaChange("error", resource_type, path, "Field disappeared."))
                elif new["schema"][path] != kind:
                    changes.append(SchemaChange("error", resource_type, path, f"Field type changed from {kind} to {new['schema'][path]}."))
            for path in sorted(set(new["schema"]) - set(old["schema"])):
                changes.append(SchemaChange("warning", resource_type, path, "Field appeared."))
            for path, length in old["arrays"].items():
                if path in new["arrays"] and new["arrays"][path] != length:
                    changes.append(SchemaChange("warning", resource_type, path, f"Observed array length changed from {length} to {new['arrays'][path]}."))
        return tuple(changes)

    @staticmethod
    def write(snapshot: SchemaSnapshot, destination: Path) -> Path:
        data = {"schema": "control_center.kfc_schema_snapshot.v1", "build_id": snapshot.build_id,
                "fingerprint": snapshot.fingerprint, "resources": snapshot.resources}
        destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(destination)
        return destination

    @staticmethod
    def _merge_by_type(resources: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for entry in resources.values():
            kind = entry["resource_type"]
            target = merged.setdefault(kind, {"schema": {}, "arrays": {}})
            target["schema"].update(entry.get("schema", {}))
            target["arrays"].update(entry.get("arrays", {}))
        return merged

    @staticmethod
    def _fingerprint(build_id: str | None, resources: dict[str, dict[str, Any]]) -> str:
        payload = {"build_id": build_id, "resources": resources}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
