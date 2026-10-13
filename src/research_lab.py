"""Read-only Research Lab browser model over authoritative catalog records."""
from __future__ import annotations

from typing import Any, Iterable

from .research_index import search
from .provenance_graph import build_provenance_graph
from .build_diff import diff_builds
from .review_queue import build_review_queue
from .research_index import content_creator_handoff
from .publication import build_web_publication


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


def build_comparison_view(records: Iterable[dict[str, Any]], from_build: str, to_build: str) -> dict[str, Any]:
    """Expose a build diff as a read-only Lab view."""
    comparison = diff_builds(records, from_build, to_build)
    comparison.update({"read_only": True, "actions": [], "runtime_approval": False})
    return comparison


def contradiction_review_view(records: Iterable[dict[str, Any]], contradictions: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Expose evidence gaps and contradiction history without resolving anything."""
    queue = build_review_queue(records, contradictions)
    return {
        "schema_version": queue["schema_version"],
        "read_only": True,
        "actions": [],
        "runtime_approval": False,
        "evidence_gap_records": queue["records"],
        "open_contradictions": queue["open_contradictions"],
    }


def content_creator_view(records: Iterable[dict[str, Any]], ids: Iterable[str] | None = None,
                         contradictions: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Expose the existing sanitized Content Creator handoff in the Lab."""
    handoff = content_creator_handoff(records, ids=ids, contradictions=contradictions)
    handoff.update({"read_only": True, "actions": [], "runtime_approval": False})
    return handoff


def web_publication_preview(records: Iterable[dict[str, Any]], reviewed_ids: set[str]) -> dict[str, Any]:
    """Preview sanitized Web Catalog output without publishing it."""
    publication = build_web_publication(records, reviewed_ids=reviewed_ids)
    return {
        "schema_version": 1,
        "application_state": "research-only",
        "read_only": True,
        "public": False,
        "publication_approval": False,
        "actions": [],
        "publication": publication,
    }


def control_center_handoff_preview(records: Iterable[dict[str, Any]], ids: Iterable[str] | None = None,
                                   contradictions: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build a plan-only Control Center handoff preview."""
    handoff = content_creator_handoff(records, ids=ids, contradictions=contradictions)
    return {
        "schema_version": 1,
        "application_state": handoff["application_state"],
        "control_center_authority": True,
        "approval_required": True,
        "approval_granted": False,
        "execution": False,
        "read_only": True,
        "runtime_approval": False,
        "actions": [],
        "records": handoff["records"],
    }
