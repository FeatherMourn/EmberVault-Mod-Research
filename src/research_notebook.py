"""Structured offline research notebook entries linked to catalog records."""
from __future__ import annotations

from typing import Any, Iterable

ENTRY_KINDS = {"note", "comparison", "experiment-reference"}


def build_notebook(entries: Iterable[dict[str, Any]], record_ids: Iterable[str]) -> dict[str, Any]:
    """Validate and build a deterministic notebook view without catalog mutation."""
    known = set(record_ids)
    normalized = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("kind") not in ENTRY_KINDS:
            raise ValueError("unsupported notebook entry kind")
        if not isinstance(entry.get("id"), str) or not entry["id"].strip():
            raise ValueError("notebook entry id is required")
        if not isinstance(entry.get("text"), str) or not entry["text"].strip():
            raise ValueError("notebook entry text is required")
        links = entry.get("record_ids", [])
        if not isinstance(links, list) or any(link not in known for link in links):
            raise ValueError("notebook links must reference known catalog records")
        normalized.append({
            "id": entry["id"], "kind": entry["kind"], "text": entry["text"].strip(),
            "record_ids": sorted(set(links)),
        })
    normalized.sort(key=lambda item: item["id"])
    if len({entry["id"] for entry in normalized}) != len(normalized):
        raise ValueError("duplicate notebook entry id")
    return {
        "schema_version": 1,
        "application_state": "research-only",
        "read_only": True,
        "runtime_approval": False,
        "actions": [],
        "entries": normalized,
    }
