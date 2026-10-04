"""Canonical research identities and duplicate detection without record mutation."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
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


def near_duplicate_pairs(records: Iterable[dict[str, Any]], threshold: float = 0.88) -> list[dict[str, Any]]:
    """Flag similar same-kind identities for review; never classify them as duplicates."""
    items = list(records)
    pairs = []
    for index, left in enumerate(items):
        left_text = json.dumps(_normalize(left.get("identity", {})), sort_keys=True)
        for right in items[index + 1:]:
            if left.get("kind") != right.get("kind"):
                continue
            right_text = json.dumps(_normalize(right.get("identity", {})), sort_keys=True)
            score = SequenceMatcher(None, left_text, right_text).ratio()
            if score >= threshold and identity_key(left, include_build=False) != identity_key(right, include_build=False):
                pairs.append({"left": left["id"], "right": right["id"], "similarity": round(score, 4),
                              "builds": sorted(set(left.get("build_scope", [])) | set(right.get("build_scope", [])))})
    return sorted(pairs, key=lambda item: (item["left"], item["right"]))
