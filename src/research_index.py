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
           build: str | None = None, kind: str | None = None) -> list[dict[str, Any]]:
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
        haystack = json.dumps(record, sort_keys=True).casefold()
        if needle and needle not in haystack:
            continue
        matches.append(record)
    return sorted(matches, key=lambda item: item["id"])
