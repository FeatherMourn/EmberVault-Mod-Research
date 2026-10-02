"""Validate structured runtime evidence for reversible tuning probes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(path: Path, expected_build: str | None = None) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"schema": "control_center.tuning_runtime_evidence_verification.v1", "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.balancing_table_scalar_write_runtime_evidence.v1":
        errors.append("unsupported tuning runtime evidence schema")
    if expected_build and data.get("target_build") != expected_build:
        errors.append("target build does not match expected build")
    runtime = data.get("runtime", {})
    required = {
        "write_ok": True, "readback_ok": True, "restore_ok": True,
        "restored_ok": True, "panic": False, "probe_removed": True,
        "stable_profile_restored": True,
    }
    for key, expected in required.items():
        if runtime.get(key) is not expected:
            errors.append(f"runtime.{key} must be {expected!r}")
    if runtime.get("readback_value") != runtime.get("test_value"):
        errors.append("readback value does not match test value")
    if runtime.get("restored_value") != runtime.get("original_value"):
        errors.append("restored value does not match original value")
    if data.get("status") != "experimental":
        errors.append("tuning write evidence must remain experimental")
    return {"schema": "control_center.tuning_runtime_evidence_verification.v1", "valid": not errors, "errors": errors, "state": data.get("status")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-build")
    args = parser.parse_args()
    result = verify(args.evidence, args.expected_build)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
