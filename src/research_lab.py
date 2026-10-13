"""Read-only Research Lab browser model over authoritative catalog records."""
from __future__ import annotations

from typing import Any, Iterable

from .research_index import search


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
