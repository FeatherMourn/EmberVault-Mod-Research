"""Fail-closed verifier for the animation-graph identity clone session."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "control_center.animation_graph_clone_evidence_verification.v1"
TYPE = "keen::anim_graph::runtime_graph::AnimationGraphResource2_0"
DONOR = "0022fed6-0380-4125-be31-ba8b5fdcbfcd"
CLONE = "7d3109de-80a7-44ad-a549-680460153d46"

def verify(path: Path, expected_build: str, expected_api: str) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"schema": SCHEMA, "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.animation_graph_identity_clone_runtime_evidence.v1": errors.append("unsupported evidence schema")
    if data.get("game_build") != expected_build: errors.append("game build mismatch")
    if data.get("loader_api_version") != expected_api: errors.append("loader API mismatch")
    if data.get("resource_type") != TYPE or data.get("donor_guid") != DONOR or data.get("clone_guid") != CLONE: errors.append("resource identity mismatch")
    if DONOR == CLONE: errors.append("clone identity is not unique")
    for field in ("explicit_unique_guid", "readback_found"):
        if data.get("registration", {}).get(field) is not True: errors.append(f"registration {field} is not verified")
    if data.get("donor") != {"preserved": True, "nodes": 108, "dependencies": 32}: errors.append("donor preservation mismatch")
    if data.get("clone") != {"nodes": 108, "dependencies": 32}: errors.append("clone inventory mismatch")
    if data.get("parity") != {"nodes": True, "node_types": True, "dependencies": True}: errors.append("clone parity mismatch")
    for field in ("animation", "entity", "world", "save"):
        if data.get("attachments", {}).get(field) is not False: errors.append(f"unexpected attachment: {field}")
    if data.get("result") != "animation_graph_identity_clone_complete": errors.append("completion marker is missing")
    if data.get("current_session_errors") != []: errors.append("current session contains errors")
    for field in ("game_stopped", "probe_uninstalled", "stable_profile_restored", "isolation_ready"):
        if data.get("cleanup", {}).get(field) is not True: errors.append(f"cleanup {field} is not verified")
    if not data.get("limitations"): errors.append("limitations must remain documented")
    return {"schema": SCHEMA, "valid": not errors, "state": "research-only", "promotion_ready": False, "identity_clone_verified": not errors, "errors": errors}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path); parser.add_argument("--expected-build", required=True); parser.add_argument("--expected-api", required=True)
    args = parser.parse_args(); result = verify(args.evidence, args.expected_build, args.expected_api)
    print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["valid"] else 1

if __name__ == "__main__": raise SystemExit(main())
