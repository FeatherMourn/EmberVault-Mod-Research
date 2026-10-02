"""Read-only relationship graph for extracted KFC donor resources."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


GUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
HASH_RE = re.compile(r"^[0-9a-fA-F]{32}$")


@dataclass(frozen=True)
class RelationshipNode:
    node_id: str
    kind: str
    label: str


@dataclass(frozen=True)
class RelationshipEdge:
    source: str
    target: str
    field: str
    reference_kind: str


@dataclass(frozen=True)
class RelationshipGraph:
    nodes: tuple[RelationshipNode, ...]
    edges: tuple[RelationshipEdge, ...]
    fingerprint: str


class DonorRelationshipExplorer:
    """Infer only explicit GUID/hash-shaped references; never invent links."""

    def scan(self, root: Path) -> RelationshipGraph:
        root = Path(root).resolve()
        nodes: dict[str, RelationshipNode] = {}
        edges: set[RelationshipEdge] = set()
        for path in sorted(root.rglob("*.json")):
            if not path.is_file() or path.is_symlink():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                continue
            source = f"resource:{path.relative_to(root).as_posix()}"
            nodes[source] = RelationshipNode(source, "resource", path.parent.name)
            self._walk(data, source, "", nodes, edges)
        ordered_nodes = tuple(sorted(nodes.values(), key=lambda node: node.node_id))
        ordered_edges = tuple(sorted(edges, key=lambda edge: (edge.source, edge.target, edge.field)))
        digest = hashlib.sha256()
        for node in ordered_nodes:
            digest.update(f"node|{node.node_id}|{node.kind}|{node.label}\n".encode())
        for edge in ordered_edges:
            digest.update(f"edge|{edge.source}|{edge.target}|{edge.field}|{edge.reference_kind}\n".encode())
        return RelationshipGraph(ordered_nodes, ordered_edges, digest.hexdigest())

    def find_references(self, root: Path, target_guid: str,
                        field_contains: str | None = None) -> tuple[RelationshipEdge, ...]:
        """Return explicit extracted-resource edges to one GUID."""
        target = str(target_guid).strip().lower()
        if not GUID_RE.fullmatch(target):
            raise ValueError("target_guid must be a GUID.")
        graph = self.scan(root)
        matches = [edge for edge in graph.edges
                   if edge.reference_kind == "guid" and edge.target == f"guid:{target}"
                   and (field_contains is None or str(field_contains) in edge.field)]
        return tuple(sorted(matches, key=lambda edge: (edge.source, edge.field)))

    def find_references_in_files(self, files: list[Path], target_guid: str,
                                 field_contains: str | None = None) -> tuple[RelationshipEdge, ...]:
        """Trace one GUID in an explicit file set without scanning an entire corpus."""
        target = str(target_guid).strip().lower()
        if not GUID_RE.fullmatch(target):
            raise ValueError("target_guid must be a GUID.")
        edges: set[RelationshipEdge] = set()
        for raw_path in files:
            path = Path(raw_path).resolve()
            if not path.is_file() or path.is_symlink():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                continue
            nodes: dict[str, RelationshipNode] = {}
            source = f"resource:{path.as_posix()}"
            self._walk(data, source, "", nodes, edges)
        return tuple(sorted(
            (edge for edge in edges
             if edge.reference_kind == "guid" and edge.target == f"guid:{target}"
             and (field_contains is None or str(field_contains) in edge.field)),
            key=lambda edge: (edge.source, edge.field),
        ))

    @staticmethod
    def _walk(value: Any, source: str, field: str, nodes: dict[str, RelationshipNode],
              edges: set[RelationshipEdge]) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_field = f"{field}.{key}" if field else str(key)
                DonorRelationshipExplorer._walk(child, source, child_field, nodes, edges)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                DonorRelationshipExplorer._walk(child, source, f"{field}[{index}]", nodes, edges)
        elif isinstance(value, str):
            reference_kind = "guid" if GUID_RE.fullmatch(value) else ("content_hash" if HASH_RE.fullmatch(value) else None)
            if reference_kind:
                target = f"{reference_kind}:{value.lower()}"
                nodes.setdefault(target, RelationshipNode(target, reference_kind, value.lower()))
                edges.add(RelationshipEdge(source, target, field, reference_kind))
