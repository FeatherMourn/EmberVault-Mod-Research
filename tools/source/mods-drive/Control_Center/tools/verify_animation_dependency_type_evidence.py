"""Verify metadata-only type resolution for animation graph dependencies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "control_center.animation_dependency_type_evidence_verification.v1"
TYPE_COUNTS = {
    "keen::AnimationSequenceContainer": 8,
    "keen::JointAnimation": 30,
    "keen::LveAnimation": 1,
    "keen::ModelHierarchyResource": 1,
    "keen::RenderClothColliderResource": 1,
    "keen::RootMotionAnimation": 1,
}


def verify(path: Path, expected_build: str, expected_api: str) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"schema": SCHEMA, "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.animation_dependency_type_runtime_evidence.v1":
        errors.append("unsupported evidence schema")
    if data.get("game_build") != expected_build:
        errors.append("game build mismatch")
    if data.get("loader_api_version") != expected_api:
        errors.append("loader API mismatch")
    if data.get("read_only") is not True or data.get("api") != "game.assets.get_resource_metadata_by_guid":
        errors.append("metadata-only GUID lookup is not verified")
    expected_summary = {"requested_guids": 32, "resolved_guids": 32, "unresolved_guids": 0, "resource_matches": 42}
    if data.get("summary") != expected_summary:
        errors.append("resolution summary mismatch")
    if data.get("resource_type_counts") != TYPE_COUNTS or sum(TYPE_COUNTS.values()) != 42:
        errors.append("resource type counts mismatch")
    structural = data.get("structural_dependencies", {})
    if structural.get("f46c0d0d-2c8c-4189-8893-edb74832529c") != ["keen::ModelHierarchyResource"]:
        errors.append("model hierarchy type is not verified")
    if structural.get("560ef428-7854-4249-9466-7188a4b4ac7a") != ["keen::RenderClothColliderResource"]:
        errors.append("cloth collider type is not verified")
    multi = data.get("multi_typed_guids", {})
    if len(multi) != 9 or len(multi.get("51a6c90c-8a85-4095-9816-4d59f97a0006", [])) != 3:
        errors.append("multi-type GUID inventory mismatch")
    for field in ("animation", "entity", "world", "save"):
        if data.get("attachments", {}).get(field) is not False:
            errors.append(f"unexpected attachment: {field}")
    if data.get("result") != "dependency_type_resolution_complete":
        errors.append("completion marker is missing")
    if data.get("current_session_errors") != []:
        errors.append("current session contains errors")
    for field in ("game_stopped", "probe_uninstalled", "stable_profile_restored", "isolation_ready"):
        if data.get("cleanup", {}).get(field) is not True:
            errors.append(f"cleanup {field} is not verified")
    if not data.get("limitations"):
        errors.append("limitations must remain documented")
    return {
        "schema": SCHEMA,
        "valid": not errors,
        "state": "research-only",
        "promotion_ready": False,
        "resolved_guids": 32 if not errors else None,
        "resource_matches": 42 if not errors else None,
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
