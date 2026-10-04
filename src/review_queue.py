"""Evidence-gap and contradiction review summaries for the local catalog."""
from __future__ import annotations

from typing import Any, Iterable


def build_review_queue(records: Iterable[dict[str, Any]], contradictions: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Return a deterministic queue without changing catalog records."""
    gaps = []
    for record in sorted(records, key=lambda item: item["id"]):
        questions = list(record.get("open_questions", []))
        limitations = list(record.get("unsupported_claims", []))
        if questions or limitations or record.get("state") in {"blocked", "unverified"}:
            gaps.append({"id": record["id"], "state": record["state"], "confidence": record.get("confidence"),
                         "open_questions": questions, "unsupported_claims": limitations,
                         "evidence_count": len(record.get("evidence", []))})
    return {"schema_version": 1, "records": gaps,
            "open_contradictions": sorted(contradictions, key=lambda item: item["id"])}
