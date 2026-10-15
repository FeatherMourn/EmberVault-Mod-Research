"""Deterministic relationships derived from read-only EML inventory records."""
from __future__ import annotations

from typing import Any, Iterable


def build_inventory_relationships(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    edges: set[tuple[str, str, str]] = set()
    for record in records:
        identity = record.get("identity", {})
        kind = record.get("kind")
        record_id = record.get("id")
        if not record_id or not kind:
            continue
        if kind == "eml-resource-type" and identity.get("resource_type"):
            edges.add((f"record:{record_id}", "classified-as", f"resource-type:{identity['resource_type']}"))
        if kind == "eml-resource-observation":
            resource_type = identity.get("resource_type")
            guid = identity.get("guid")
            if resource_type:
                edges.add((f"record:{record_id}", "instance-of", f"resource-type:{resource_type}"))
            if guid:
                edges.add((f"record:{record_id}", "identified-by", f"guid:{guid}"))
    return {"schema_version": 1, "read_only": True, "runtime_approval": False,
            "edges": [{"source": source, "relation": relation, "target": target}
                      for source, relation, target in sorted(edges)]}
