"""Verify that a research launch observed both EML and the game process."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(path: Path) -> dict:
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "control_center.research_session_launch_verification.v1", "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.research_session_launch.v1":
        errors.append("unsupported launch evidence schema")
    if data.get("fresh_session_observed") is not True:
        errors.append("fresh EML session was not observed")
    if data.get("game_process_observed") is not True:
        errors.append("game process was not observed")
    if not isinstance(data.get("log"), str) or not data.get("log"):
        errors.append("launch log path is missing")
    return {"schema": "control_center.research_session_launch_verification.v1", "valid": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    result = verify(args.evidence)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
