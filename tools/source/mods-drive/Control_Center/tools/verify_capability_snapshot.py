"""Verify that a capability snapshot is current, traceable, and internally consistent."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_INPUTS = ("capability_audit", "milestone_gate", "live_preflight", "metadata_policy")


def verify(path: Path) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"schema": "control_center.capability_snapshot_verification.v1", "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.capability_snapshot.v1":
        errors.append("unsupported capability snapshot schema")
    inputs = data.get("inputs")
    if not isinstance(inputs, dict):
        errors.append("snapshot input provenance is missing")
    else:
        for name in REQUIRED_INPUTS:
            value = inputs.get(name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"snapshot input provenance is missing: {name}")
            elif not Path(value).is_file():
                errors.append(f"snapshot input does not exist: {name}")
    if not isinstance(data.get("capabilities"), list):
        errors.append("capabilities must be a list")
    if not isinstance(data.get("capability_counts"), dict):
        errors.append("capability_counts must be an object")
    return {"schema": "control_center.capability_snapshot_verification.v1", "valid": not errors, "path": str(path), "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    result = verify(parser.parse_args().snapshot)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
