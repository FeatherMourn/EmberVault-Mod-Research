"""Read-only Research Lab browser model over authoritative catalog records."""
from __future__ import annotations

from typing import Any, Iterable

from .research_index import search
from .provenance_graph import build_provenance_graph


def build_lab_snapshot(records: Iterable[dict[str, Any]], *, query: str = "",
                       state: str | None = None, build: str | None = None,
                       kind: str | None = None, confidence: str | None = None,
                       has_open_questions: bool | None = None) -> dict[str, Any]:
    """Build a deterministic browser snapshot without copying or mutating records."""
    matches = search(records, query, state=state, build=build, kind=kind,
                     confidence=confidence, has_open_questions=has_open_questions)
    return {
        "schema_version": 1,
        "application_state": "research-only",
        "read_only": True,
        "actions": [],
        "count": len(matches),
        "records": [
            {
                "id": record["id"],
                "kind": record["kind"],
                "identity": record.get("identity", {}),
                "build_scope": record.get("build_scope", []),
                "state": record["state"],
                "confidence": record.get("confidence", "unknown"),
                "evidence_count": len(record.get("evidence", [])),
                "open_question_count": len(record.get("open_questions", [])),
                "contradiction_count": len(record.get("contradictions", [])),
                "runtime_approval": False,
            }
            for record in matches
        ],
    }


def record_detail(record: dict[str, Any]) -> dict[str, Any]:
    """Return a bounded detail view preserving evidence and limitations."""
    return {
        "schema_version": 1,
        "read_only": True,
        "actions": [],
        "runtime_approval": False,
        "record": dict(record),
    }


def relationship_view(records: Iterable[dict[str, Any]], record_id: str) -> dict[str, Any]:
    """Return the selected record's read-only provenance neighborhood."""
    graph = build_provenance_graph(records)
    selected = f"record:{record_id}"
    edges = [edge for edge in graph["edges"] if edge["source"] == selected or edge["target"] == selected]
    node_ids = {selected}
    for edge in edges:
        node_ids.update((edge["source"], edge["target"]))
    return {
        "schema_version": 1,
        "read_only": True,
        "actions": [],
        "record_id": record_id,
        "nodes": [node for node in graph["nodes"] if node["id"] in node_ids],
        "edges": edges,
    }


def evidence_navigation(records: Iterable[dict[str, Any]], evidence_path: str) -> dict[str, Any]:
    """Find records supported by one evidence path without exposing mutation controls."""
    matches = [record for record in records if evidence_path in record.get("evidence", [])]
    return {
        "schema_version": 1,
        "read_only": True,
        "actions": [],
        "evidence_path": evidence_path,
        "records": [{"id": record["id"], "kind": record["kind"], "state": record["state"]}
                    for record in sorted(matches, key=lambda item: item["id"])],
    }


def facet_summary(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Return deterministic counts for browsing and review prioritization."""
    records = list(records)

    def counts(values):
        result: dict[str, int] = {}
        for value in values:
            result[str(value)] = result.get(str(value), 0) + 1
        return dict(sorted(result.items()))

    return {
        "schema_version": 1,
        "read_only": True,
        "actions": [],
        "record_count": len(records),
        "by_kind": counts(record.get("kind", "unknown") for record in records),
        "by_state": counts(record.get("state", "unknown") for record in records),
        "by_confidence": counts(record.get("confidence", "unknown") for record in records),
        "by_build": counts(build for record in records for build in record.get("build_scope", [])),
        "evidence_gaps": sorted(record["id"] for record in records if record.get("open_questions")),
        "contradiction_records": sorted(record["id"] for record in records if record.get("contradictions")),
    }
