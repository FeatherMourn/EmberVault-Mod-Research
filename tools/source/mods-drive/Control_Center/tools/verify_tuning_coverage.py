"""Verify build-scoped tuning coverage and research queue evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(path: Path, expected_build: str = "1076226") -> dict:
    errors: list[str] = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"schema": "control_center.tuning_coverage_verification.v1", "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.tuning_coverage.v1":
        errors.append("unsupported tuning coverage schema")
    if str(data.get("build")) != str(expected_build):
        errors.append("tuning coverage build does not match the pinned build")
    families = data.get("families")
    queue = data.get("research_queue")
    if not isinstance(families, list) or not families:
        errors.append("families must be a non-empty list")
    if not isinstance(queue, list):
        errors.append("research_queue must be a list")
    if isinstance(families, list):
        ids = [item.get("family") for item in families if isinstance(item, dict)]
        if len(ids) != len(set(ids)):
            errors.append("tuning families are duplicated")
        if any(item.get("state") not in {"covered", "uncovered"} for item in families if isinstance(item, dict)):
            errors.append("tuning family has an invalid state")
    if isinstance(queue, list):
        if any(not isinstance(item, dict) or not str(item.get("family", "")).strip() for item in queue):
            errors.append("research queue contains an invalid family entry")
    return {"schema": "control_center.tuning_coverage_verification.v1", "valid": not errors,
            "path": str(Path(path).resolve()), "family_count": len(families) if isinstance(families, list) else 0,
            "queue_count": len(queue) if isinstance(queue, list) else 0, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("coverage", type=Path)
    parser.add_argument("--expected-build", default="1076226")
    args = parser.parse_args()
    result = verify(args.coverage, args.expected_build)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
