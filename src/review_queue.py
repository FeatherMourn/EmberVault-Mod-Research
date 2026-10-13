"""Evidence-gap and contradiction review summaries for the local catalog."""
from __future__ import annotations

from typing import Any, Iterable


def evidence_score(record: dict[str, Any], *, contradiction_count: int = 0) -> int:
    """Score recorded support only; this never implies runtime validity."""
    confidence = {"high": 4, "medium": 3, "bounded": 2, "offline-fixture": 2,
                  "low": 1, "unknown": 0}.get(record.get("confidence", "unknown"), 0)
    score = min(len(record.get("evidence", [])), 3) + confidence
    score -= min(len(record.get("open_questions", [])), 3)
    score -= min(len(record.get("unsupported_claims", [])), 2)
    score -= min(contradiction_count, 2) * 2
    return max(0, min(10, score))


def build_review_queue(records: Iterable[dict[str, Any]], contradictions: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Return a deterministic queue without changing catalog records."""
    contradictions = list(contradictions)
    contradiction_counts: dict[str, int] = {}
    for contradiction in contradictions:
        record_id = contradiction.get("record_id")
        if record_id:
            contradiction_counts[record_id] = contradiction_counts.get(record_id, 0) + 1
    gaps = []
    for record in records:
        questions = list(record.get("open_questions", []))
        limitations = list(record.get("unsupported_claims", []))
        contradiction_count = contradiction_counts.get(record["id"], 0) + len(record.get("contradictions", []))
        if questions or limitations or contradiction_count or record.get("state") in {"blocked", "unverified"}:
            score = evidence_score(record, contradiction_count=contradiction_count)
            gaps.append({"id": record["id"], "state": record["state"], "confidence": record.get("confidence"),
                         "open_questions": questions, "unsupported_claims": limitations,
                         "evidence_count": len(record.get("evidence", [])),
                         "contradiction_count": contradiction_count, "evidence_score": score,
                         "priority": "high" if score <= 3 or contradiction_count else "normal"})
    gaps.sort(key=lambda item: (item["priority"] != "high", item["evidence_score"], item["id"]))
    return {"schema_version": 1, "records": gaps,
            "open_contradictions": sorted(contradictions, key=lambda item: item["id"])}
