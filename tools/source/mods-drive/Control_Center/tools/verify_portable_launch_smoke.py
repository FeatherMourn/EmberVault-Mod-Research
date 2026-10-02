"""Validate a portable Control Center launch-smoke evidence record."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(path: Path) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "control_center.portable_launch_smoke_verification.v1", "valid": False, "errors": [str(exc)]}
    if data.get("schema") not in {"control_center.portable_launch_smoke.v1", "control_center.portable_launch_smoke.v2"}: errors.append("unsupported schema")
    if data.get("schema") == "control_center.portable_launch_smoke.v1" and data.get("version") != "1.0.2": errors.append("version must be 1.0.2")
    for key in ("launch_observed", "process_responding", "clean_shutdown_observed"):
        if data.get(key) is not True: errors.append(f"{key} must be true")
    if data.get("game_started") is not False: errors.append("game_started must be false")
    if data.get("status") != "passed": errors.append("status must be passed")
    if data.get("schema") == "control_center.portable_launch_smoke.v2" and data.get("remaining_pids") != []: errors.append("process tree was not fully terminated")
    verification_schema = "control_center.portable_launch_smoke_verification.v2" if data.get("schema") == "control_center.portable_launch_smoke.v2" else "control_center.portable_launch_smoke_verification.v1"
    return {"schema": verification_schema, "valid": not errors,
            "path": str(path), "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    result = validate(parser.parse_args().evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
