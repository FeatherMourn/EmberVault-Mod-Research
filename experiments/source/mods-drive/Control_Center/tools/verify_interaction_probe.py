"""Verify that an interaction donor probe is research-only and safe to install."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = "control_center.interaction_donor_probe.v1"
GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")


def verify(path: Path, expected_build: str | None = None) -> dict:
    errors: list[str] = []
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "control_center.interaction_probe_verification.v1", "valid": False, "errors": [str(exc)]}

    if manifest.get("schema") != SCHEMA:
        errors.append("unsupported or missing interaction probe schema")
    if expected_build and manifest.get("target_build") not in (expected_build, expected_build.split("|", 1)[0]):
        errors.append("probe target build does not match the requested build")
    for field in ("id", "resource_type", "donor_guid", "entrypoint", "execution_scope"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            errors.append(f"missing non-empty field: {field}")
    if isinstance(manifest.get("donor_guid"), str) and not GUID.fullmatch(manifest["donor_guid"]):
        errors.append("donor_guid must be a UUID, not a placeholder")
    if manifest.get("feature_state") != "research-only":
        errors.append("interaction probes must be research-only")
    if manifest.get("runtime_mutation") is not False:
        errors.append("runtime_mutation must be false")
    if manifest.get("execution_scope") != "single-player-read-only":
        errors.append("execution_scope must be single-player-read-only")
    for field in ("authority", "persistence", "replication"):
        if manifest.get(field) != "unknown":
            errors.append(f"{field} must remain unknown until runtime evidence exists")
    prohibited = manifest.get("prohibited_actions")
    if not isinstance(prohibited, list) or not prohibited:
        errors.append("prohibited_actions must be a non-empty list")
    outputs = manifest.get("evidence_outputs")
    if not isinstance(outputs, list) or not outputs:
        errors.append("evidence_outputs must be a non-empty list")
    if manifest.get("save_policy") != "do-not-save-until-explicitly-approved":
        errors.append("save_policy must prevent unapproved saves")
    if manifest.get("rollback_policy") != "restore-probe-and-profile-before-leaving-session":
        errors.append("rollback_policy must restore the probe and profile")
    return {
        "schema": "control_center.interaction_probe_verification.v1",
        "valid": not errors,
        "path": str(path.resolve()),
        "id": manifest.get("id"),
        "feature_state": manifest.get("feature_state"),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--expected-build")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.manifest, args.expected_build)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
