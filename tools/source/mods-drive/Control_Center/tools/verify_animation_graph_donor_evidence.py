"""Fail-closed verifier for one animation-graph donor payload readback."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "control_center.animation_graph_donor_evidence_verification.v1"
TYPE = "keen::anim_graph::runtime_graph::AnimationGraphResource2_0"
GUID = "0022fed6-0380-4125-be31-ba8b5fdcbfcd"


def verify(path: Path, expected_build: str, expected_api: str) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"schema": SCHEMA, "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.animation_graph_single_donor_runtime_evidence.v1":
        errors.append("unsupported evidence schema")
    if data.get("game_build") != expected_build:
        errors.append("game build mismatch")
    if data.get("loader_api_version") != expected_api:
        errors.append("loader API mismatch")
    if data.get("resource_type") != TYPE or data.get("donor_guid") != GUID:
        errors.append("resource donor identity mismatch")
    if data.get("read_only") is not True:
        errors.append("probe was not read-only")
    lookup = data.get("resource_lookup", {})
    for field in ("ok", "found", "guid_matches"):
        if lookup.get(field) is not True:
            errors.append(f"resource lookup {field} is not verified")
    payload = data.get("payload_read", {})
    if payload.get("ok") is not True or payload.get("data_type") != "userdata":
        errors.append("typed payload readback is not verified")
    fields = data.get("fields", {})
    expected_fields = {
        "hierarchy": "f46c0d0d-2c8c-4189-8893-edb74832529c",
        "node_definitions_count": 108,
        "slot_bone_index_mapping_count": 36,
        "used_input_id_count": 26,
        "root_node": 3143804083,
        "post_process_root_node": 0,
    }
    for field, expected in expected_fields.items():
        if fields.get(field) != expected:
            errors.append(f"field mismatch: {field}")
    attachments = data.get("attachments", {})
    for field in ("animation", "entity", "world", "save"):
        if attachments.get(field) is not False:
            errors.append(f"unexpected attachment: {field}")
    if data.get("result") != "single_animation_graph_payload_read_complete":
        errors.append("completion marker is missing")
    if data.get("current_session_errors") != []:
        errors.append("current session contains errors")
    cleanup = data.get("cleanup", {})
    for field in ("game_stopped", "probe_uninstalled", "stable_profile_restored", "isolation_ready"):
        if cleanup.get(field) is not True:
            errors.append(f"cleanup {field} is not verified")
    if not data.get("limitations"):
        errors.append("limitations must remain documented")
    return {
        "schema": SCHEMA,
        "valid": not errors,
        "state": "research-only",
        "promotion_ready": False,
        "verified_node_count": fields.get("node_definitions_count"),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-build", required=True)
    parser.add_argument("--expected-api", required=True)
    args = parser.parse_args()
    result = verify(args.evidence, args.expected_build, args.expected_api)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
