"""Verify that a research probe was removed and the stable profile relaunched cleanly."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(path: Path, expected_build: str | None = None) -> dict[str, object]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "control_center.post_rollback_stable_launch_verification.v1",
                "valid": False, "path": str(path), "errors": [str(exc)]}
    if data.get("schema") != "control_center.post_rollback_stable_launch_evidence.v1":
        errors.append("unexpected evidence schema")
    if expected_build and data.get("game_build") != expected_build:
        errors.append("game build does not match expected build")
    if data.get("fresh_session_observed") is not True:
        errors.append("fresh stable session was not observed")
    profile = data.get("stable_profile")
    if not isinstance(profile, dict):
        errors.append("stable_profile is missing")
    else:
        if profile.get("research_only_mods") != []:
            errors.append("research-only modules remain in stable profile")
        if profile.get("unclassified_mods") != []:
            errors.append("unclassified modules remain in stable profile")
        if profile.get("isolation_ready") is not True or profile.get("status") != "ready":
            errors.append("stable profile is not ready and isolated")
    runtime = data.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("runtime evidence is missing")
    else:
        for field in ("stable_mod_loaded", "runtime_loader_attached"):
            if runtime.get(field) is not True:
                errors.append(f"missing successful runtime marker: {field}")
        if runtime.get("panic_or_probe_error_observed") is not False:
            errors.append("panic or probe error was observed")
        if not isinstance(runtime.get("patches_applied"), int) or runtime["patches_applied"] <= 0:
            errors.append("stable runtime did not apply patches")
    if data.get("game_stopped_after_check") is not True:
        errors.append("game shutdown was not verified")
    if data.get("rollback_verified") is not True:
        errors.append("rollback was not verified")
    return {"schema": "control_center.post_rollback_stable_launch_verification.v1",
            "valid": not errors, "path": str(path), "errors": errors}


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
