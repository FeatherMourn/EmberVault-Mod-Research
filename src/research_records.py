"""Versioned research-record migration helpers."""
from __future__ import annotations

from typing import Any, Iterable


def migrate_seed_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Upgrade seed candidates to record schema version 1 without changing claims."""
    migrated = []
    for source in records:
        record = dict(source)
        record.setdefault("supported_claims", [])
        record.setdefault("unsupported_claims", [])
        record.setdefault("open_questions", [])
        record.setdefault("contradictions", [])
        record["record_schema_version"] = 1
        migrated.append(record)
    return migrated
