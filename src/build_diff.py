"""Build-scoped, read-only research record comparison."""
from __future__ import annotations

import json
from typing import Any, Iterable

from .identity import identity_key


def _project(records: Iterable[dict[str, Any]], build: str) -> dict[str, dict[str, Any]]:
    return {identity_key(record, include_build=False): record for record in records if build in record.get("build_scope", [])}


def diff_builds(records: Iterable[dict[str, Any]], from_build: str, to_build: str) -> dict[str, Any]:
    """Compare build-scoped records while retaining source record IDs."""
    source = list(records)
    left, right = _project(source, from_build), _project(source, to_build)
    added, removed, changed = [], [], []
    for key in sorted(set(right) - set(left)):
        added.append({"id": right[key]["id"], "identity": right[key].get("identity", {})})
    for key in sorted(set(left) - set(right)):
        removed.append({"id": left[key]["id"], "identity": left[key].get("identity", {})})
    fields = ("kind", "state", "confidence", "supported_claims", "unsupported_claims", "open_questions", "evidence")
    for key in sorted(set(left) & set(right)):
        differences = {field: {"from": left[key].get(field), "to": right[key].get(field)}
                       for field in fields if left[key].get(field) != right[key].get(field)}
        if differences:
            changed.append({"from_id": left[key]["id"], "to_id": right[key]["id"], "identity": right[key].get("identity", {}), "differences": differences})
    return {"schema_version": 1, "from_build": from_build, "to_build": to_build,
            "added": added, "removed": removed, "changed": changed}
