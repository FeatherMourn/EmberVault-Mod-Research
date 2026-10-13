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


def review_priority_summary(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Summarize review pressure without changing or resolving records."""
    by_build: dict[str, dict[str, int]] = {}
    by_kind: dict[str, dict[str, int]] = {}
    for record in records:
        contradiction_count = len(record.get("contradictions", []))
        priority = "high" if contradiction_count or evidence_score(record) <= 3 else "normal"
        build = ",".join(str(value) for value in record.get("build_scope", [])) or "unscoped"
        kind = str(record.get("kind", "unknown"))
        for group, key in ((by_build, build), (by_kind, kind)):
            bucket = group.setdefault(key, {"records": 0, "high_priority": 0, "evidence_gaps": 0, "contradictions": 0})
            bucket["records"] += 1
            bucket["high_priority"] += priority == "high"
            bucket["evidence_gaps"] += bool(record.get("open_questions"))
            bucket["contradictions"] += contradiction_count > 0
    return {"schema_version": 1, "read_only": True, "runtime_approval": False,
            "actions": [], "by_build": dict(sorted(by_build.items())),
            "by_kind": dict(sorted(by_kind.items()))}


def compare_review_priority(records: Iterable[dict[str, Any]], from_build: str, to_build: str) -> dict[str, Any]:
    """Compare review pressure for two build scopes without merging records."""
    records = list(records)

    def project(build: str) -> dict[str, dict[str, Any]]:
        result = {}
        for record in records:
            if build in {str(value) for value in record.get("build_scope", [])}:
                contradictions = len(record.get("contradictions", []))
                score = evidence_score(record, contradiction_count=contradictions)
                result[record["id"]] = {"evidence_score": score,
                                        "priority": "high" if contradictions or score <= 3 else "normal",
                                        "evidence_gaps": len(record.get("open_questions", [])),
                                        "contradictions": contradictions}
        return result

    before, after = project(from_build), project(to_build)
    changed = []
    for record_id in sorted(set(before) & set(after)):
        if before[record_id] != after[record_id]:
            changed.append({"id": record_id, "from": before[record_id], "to": after[record_id]})
    return {"schema_version": 1, "read_only": True, "runtime_approval": False, "actions": [],
            "from_build": from_build, "to_build": to_build,
            "added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after)),
            "changed": changed}
