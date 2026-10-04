"""Canonical research identities and duplicate detection without record mutation."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any, Iterable


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value.strip().casefold())
    if isinstance(value, dict):
        return {str(key): _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def identity_key(record: dict[str, Any], *, include_build: bool = False) -> str:
    """Return a stable identity key; build scope is opt-in for cross-build review."""
    value: dict[str, Any] = {"kind": record["kind"], "identity": record.get("identity", {})}
    if include_build:
        value["build_scope"] = sorted(record.get("build_scope", []))
    return json.dumps(_normalize(value), sort_keys=True, separators=(",", ":"))


def duplicate_groups(records: Iterable[dict[str, Any]], *, include_build: bool = True) -> list[list[str]]:
    """Find duplicate IDs while preserving records and their provenance."""
    groups: dict[str, list[str]] = defaultdict(list)
    for record in records:
        groups[identity_key(record, include_build=include_build)].append(record["id"])
    return sorted((sorted(ids) for ids in groups.values() if len(ids) > 1), key=lambda ids: ids[0])
