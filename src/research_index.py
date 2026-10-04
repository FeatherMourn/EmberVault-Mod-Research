"""Read-only index and search helpers for normalized research candidates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

ALLOWED_STATES = {"triaged", "partially-verified", "experimental", "verified", "blocked", "unsupported"}


def load_candidates(path: Path) -> list[dict[str, Any]]:
    """Load candidate records without modifying the source file."""
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("records"), list):
        raise ValueError("unsupported candidate schema")
    records = payload["records"]
    seen: set[str] = set()
    for record in records:
        validate_record(record)
        if record["id"] in seen:
            raise ValueError(f"duplicate research record: {record['id']}")
        seen.add(record["id"])
    return records


def load_manifest(path: Path) -> dict[str, dict[str, Any]]:
    """Load the hashed intake manifest keyed by promoted relative path."""
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("records"), list):
        raise ValueError("unsupported intake manifest schema")
    manifest: dict[str, dict[str, Any]] = {}
    for record in payload["records"]:
        promoted_path = record.get("promoted_path")
        digest = record.get("sha256")
        if not isinstance(promoted_path, str) or not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("invalid intake manifest record")
        if promoted_path in manifest:
            raise ValueError(f"duplicate manifest path: {promoted_path}")
        manifest[promoted_path] = record
    return manifest


def missing_evidence(records: Iterable[dict[str, Any]], manifest: dict[str, dict[str, Any]]) -> list[str]:
    """Return evidence paths referenced by records but absent from the intake manifest."""
    missing = {path for record in records for path in record["evidence"] if path not in manifest}
    return sorted(missing)


def content_creator_handoff(records: Iterable[dict[str, Any]], ids: Iterable[str] | None = None) -> dict[str, Any]:
    """Build a sanitized, read-only handoff for design-only Content Creator work."""
    selected = list(records) if ids is None else [record for record in records if record["id"] in set(ids)]
    return {
        "schema_version": 1,
        "application_state": "design-only",
        "live_game_files_touched": False,
        "records": [
            {
                "id": record["id"],
                "kind": record["kind"],
                "identity": record["identity"],
                "build_scope": record.get("build_scope", []),
                "state": record["state"],
                "confidence": record.get("confidence"),
                "supported_claims": record.get("supported_claims", []),
                "evidence": record["evidence"],
                "unsupported_claims": record.get("unsupported_claims", []),
                "open_questions": record.get("open_questions", []),
            }
            for record in sorted(selected, key=lambda item: item["id"])
        ],
    }


def validate_record(record: dict[str, Any]) -> None:
    required = {"id", "kind", "identity", "build_scope", "state", "evidence", "open_questions"}
    missing = required.difference(record)
    if missing:
        raise ValueError(f"missing research fields: {sorted(missing)}")
    if not record["id"] or record["state"] not in ALLOWED_STATES:
        raise ValueError("invalid research identity or state")
    if not isinstance(record["evidence"], list) or not isinstance(record["open_questions"], list):
        raise ValueError("evidence and open_questions must be lists")


def search(records: Iterable[dict[str, Any]], query: str = "", *, state: str | None = None,
           build: str | None = None, kind: str | None = None, confidence: str | None = None,
           has_open_questions: bool | None = None) -> list[dict[str, Any]]:
    """Return deterministic, read-only matches across searchable record text."""
    if state is not None and state not in ALLOWED_STATES:
        raise ValueError(f"invalid state: {state}")
    needle = query.casefold().strip()
    matches = []
    for record in records:
        if state and record["state"] != state:
            continue
        if kind and record["kind"] != kind:
            continue
        if build and build not in record.get("build_scope", []):
            continue
        if confidence and record.get("confidence") != confidence:
            continue
        if has_open_questions is not None and bool(record.get("open_questions")) != has_open_questions:
            continue
        haystack = json.dumps(record, sort_keys=True).casefold()
        if needle and needle not in haystack:
            continue
        matches.append(record)
    return sorted(matches, key=lambda item: item["id"])
