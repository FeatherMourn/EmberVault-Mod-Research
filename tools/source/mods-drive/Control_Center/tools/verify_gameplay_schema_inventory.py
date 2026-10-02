"""Verify the gameplay schema inventory is discovery-only and build-scoped."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = {"interaction", "ai", "quest", "animation", "world_generation", "multiplayer_authority"}


def verify(path: Path, expected_build: str) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read inventory: {exc}"]
    if data.get("schema") != "control_center.gameplay_schema_inventory.v1":
        errors.append("invalid schema")
    if not str(data.get("build", "")).startswith(expected_build):
        errors.append("inventory build does not match expected build")
    groups = data.get("groups")
    if not isinstance(groups, list):
        return errors + ["groups must be an array"]
    names = {group.get("area") for group in groups if isinstance(group, dict)}
    errors.extend(f"missing group: {name}" for name in sorted(REQUIRED - names))
    for group in groups:
        if not isinstance(group, dict):
            errors.append("group must be an object")
            continue
        if group.get("runtime_mutation") is not False:
            errors.append(f"{group.get('area')}: runtime_mutation must be false")
        if group.get("status") != "research-only":
            errors.append(f"{group.get('area')}: status must be research-only")
        if group.get("authority") != "unknown":
            errors.append(f"{group.get('area')}: authority must be unknown")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--expected-build", default="1076226")
    args = parser.parse_args()
    errors = verify(args.path, args.expected_build)
    result = {"schema": "control_center.gameplay_schema_inventory_verification.v1", "valid": not errors, "errors": errors}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
