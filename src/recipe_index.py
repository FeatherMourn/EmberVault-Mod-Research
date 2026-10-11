"""Read-only offline recipe index for reviewed research records."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_recipe_index(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    records = payload.get("records", payload) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("recipe index must contain a records list")
    result = []
    for record in records:
        if not isinstance(record, dict) or record.get("kind") != "donor-recipe":
            continue
        identity = record.get("identity", {})
        recipe_id = identity.get("recipe_id")
        builds = record.get("build_scope", [])
        if recipe_id is None or not isinstance(builds, list):
            continue
        result.append({"id": record.get("id", ""), "recipe_id": str(recipe_id),
                       "build_scope": sorted(str(build) for build in builds),
                       "state": record.get("state", "unknown"),
                       "confidence": record.get("confidence", "unknown"),
                       "evidence": list(record.get("evidence", [])),
                       "open_questions": list(record.get("open_questions", []))})
    return sorted(result, key=lambda item: (item["recipe_id"], item["id"]))


def lookup_recipe(records: list[dict[str, Any]], recipe_id: int | str, build: str) -> dict[str, Any]:
    """Return a bounded lookup result; never infer a recipe from probe setup text."""
    target = str(recipe_id)
    matches = [record for record in records if record["recipe_id"] == target and build in record["build_scope"]]
    if not matches:
        return {"state": "unresolved", "recipe_id": target, "build": str(build),
                "matches": [], "runtime_behavior": "unverified", "read_only": True,
                "reason": "No normalized same-build donor-recipe record was found."}
    return {"state": "resolved", "recipe_id": target, "build": str(build),
            "matches": matches, "runtime_behavior": "unverified", "read_only": True}
