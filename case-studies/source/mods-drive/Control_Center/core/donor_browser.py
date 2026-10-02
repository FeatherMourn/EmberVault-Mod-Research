"""Searchable donor-resource index for the Visual Content Studio."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .relationship_graph import DonorRelationshipExplorer, RelationshipGraph
from .resource_inspector import ResourceInspector, ResourceRecord


@dataclass(frozen=True)
class DonorRecord:
    resource_type: str
    path: Path
    guid: str | None
    fields: tuple[str, ...]
    array_fields: tuple[str, ...]
    sha256: str
    search_text: str
    metadata_state: str


class DonorBrowser:
    """Index extracted donors without modifying source files."""

    def __init__(self) -> None:
        self.inspector = ResourceInspector()
        self.relationships = DonorRelationshipExplorer()

    def index(self, root: Path) -> tuple[tuple[DonorRecord, ...], RelationshipGraph]:
        root = Path(root).resolve()
        records = tuple(self._record(item) for item in self.inspector.scan(root))
        return tuple(sorted(records, key=lambda item: (item.resource_type, str(item.path)))), self.relationships.scan(root)

    @staticmethod
    def search(records: tuple[DonorRecord, ...] | list[DonorRecord], query: str = "",
               resource_type: str | None = None, field: str | None = None) -> tuple[DonorRecord, ...]:
        query = str(query).strip().lower()
        resource_type = str(resource_type).strip().lower() if resource_type else None
        field = str(field).strip().lower() if field else None
        result = []
        for record in records:
            haystack = " ".join((record.resource_type, str(record.path), record.guid or "", record.search_text)).lower()
            if query and query not in haystack:
                continue
            if resource_type and record.resource_type.lower() != resource_type:
                continue
            if field and not any(field in item.lower() for item in record.fields):
                continue
            result.append(record)
        return tuple(result)

    def _record(self, record: ResourceRecord) -> DonorRecord:
        values = []
        def collect(value: object) -> None:
            if isinstance(value, dict):
                for child in value.values(): collect(child)
            elif isinstance(value, list):
                for child in value: collect(child)
            elif isinstance(value, str):
                values.append(value)
        collect(record.data)
        policy = self.inspector.metadata_policy(record.resource_type)
        return DonorRecord(record.resource_type, record.path, record.guid,
                           tuple(sorted(record.schema)), tuple(sorted(record.arrays)), record.sha256,
                           " ".join(values), policy.get("state", "unknown"))
