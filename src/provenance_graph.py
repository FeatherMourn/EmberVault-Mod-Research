"""Deterministic, read-only provenance graph derived from research records."""
from __future__ import annotations

import hashlib
from typing import Any, Iterable


def _claim_id(record_id: str, claim: str, category: str) -> str:
    digest = hashlib.sha256(f"{record_id}|{category}|{claim}".encode()).hexdigest()[:16]
    return f"claim:{digest}"


def build_provenance_graph(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str, str]] = set()

    def node(node_id: str, kind: str, label: str) -> None:
        nodes.setdefault(node_id, {"id": node_id, "kind": kind, "label": label})

    for record in records:
        record_id = f"record:{record['id']}"
        node(record_id, "record", record["id"])
        kind_id = f"kind:{record['kind']}"
        node(kind_id, "kind", record["kind"])
        edges.add((record_id, "classified-as", kind_id))
        for build in record.get("build_scope", []):
            build_id = f"build:{build}"
            node(build_id, "build", str(build))
            edges.add((record_id, "scoped-to", build_id))
        for path in record.get("evidence", []):
            evidence_id = f"evidence:{path}"
            node(evidence_id, "evidence", path)
            edges.add((record_id, "supported-by", evidence_id))
        for category in ("supported_claims", "unsupported_claims", "open_questions"):
            for claim in record.get(category, []):
                claim_id = _claim_id(record["id"], claim, category)
                node(claim_id, category.removesuffix("s"), claim)
                edges.add((record_id, f"has-{category.removesuffix('s')}", claim_id))
    return {"schema_version": 1, "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
            "edges": [{"source": source, "relation": relation, "target": target}
                      for source, relation, target in sorted(edges)]}
