"""Deterministic resource relationships derived from research records."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def build_resource_graph(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Link shared explicit identity values without merging or inferring behavior."""
    nodes: dict[str, dict[str, Any]] = {}
    memberships: dict[tuple[str, str], list[str]] = defaultdict(list)

    for record in records:
        record_id = f"record:{record['id']}"
        nodes[record_id] = {"id": record_id, "kind": "record", "label": record["id"]}
        identity = record.get("identity", {})
        if not isinstance(identity, dict):
            continue
        for field, value in sorted(identity.items()):
            if value in (None, "", [], {}):
                continue
            token = f"identity:{field}:{value}"
            nodes.setdefault(token, {"id": token, "kind": "identity", "label": f"{field}={value}"})
            memberships[(field, str(value))].append(record_id)

    edges: set[tuple[str, str, str]] = set()
    for (field, value), record_ids in memberships.items():
        for record_id in sorted(set(record_ids)):
            edges.add((record_id, f"shares-{field}", f"identity:{field}:{value}"))

    return {
        "schema_version": 1,
        "read_only": True,
        "runtime_approval": False,
        "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
        "edges": [{"source": source, "relation": relation, "target": target}
                  for source, relation, target in sorted(edges)],
        "limitations": [
            "Relationships use only explicit recorded identity values.",
            "Shared identity does not establish runtime compatibility or behavior.",
        ],
    }
