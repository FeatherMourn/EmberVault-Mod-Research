"""Fail-closed verifier for bounded animation-graph dependency traversal."""
from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path


SCHEMA = "control_center.animation_graph_dependency_evidence_verification.v1"
EVIDENCE_SCHEMA = "control_center.animation_graph_dependency_runtime_evidence.v1"
TYPE = "keen::anim_graph::runtime_graph::AnimationGraphResource2_0"
GUID = "0022fed6-0380-4125-be31-ba8b5fdcbfcd"
EXPECTED_NODE_TYPES = {
    "keen::anim_graph::runtime_graph::SampleAnimationClipNodeDefinition": 26,
    "keen::anim_graph::runtime_graph::BlendSpace_1DNodeDefinition": 1,
    "keen::anim_graph::runtime_graph::PoseResultNodeDefinition": 27,
    "keen::anim_graph::runtime_graph::IdParameterEqualsConstantNodeDefinition": 26,
    "keen::anim_graph::runtime_graph::StateMachineStateNodeDefinition": 26,
    "keen::anim_graph::runtime_graph::LayerBlendNodeDefinition": 1,
    "keen::anim_graph::runtime_graph::StateMachineNodeDefinition": 1,
}


def verify(path: Path, expected_build: str, expected_api: str) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"schema": SCHEMA, "valid": False, "errors": [str(exc)]}
    if data.get("schema") != EVIDENCE_SCHEMA:
        errors.append("unsupported evidence schema")
    if data.get("game_build") != expected_build:
        errors.append("game build mismatch")
    if data.get("loader_api_version") != expected_api:
        errors.append("loader API mismatch")
    if data.get("resource_type") != TYPE or data.get("donor_guid") != GUID:
        errors.append("resource donor identity mismatch")
    if data.get("read_only") is not True:
        errors.append("probe was not read-only")
    bounds = data.get("bounds", {})
    if bounds.get("maximum_nodes") != 128 or bounds.get("visited_nodes") != 108:
        errors.append("bounded traversal does not match the verified session")
    node_types = data.get("node_types", {})
    if node_types != EXPECTED_NODE_TYPES or sum(node_types.values()) != 108:
        errors.append("node type inventory mismatch")
    dependencies = data.get("dependencies", [])
    dependency_guids = [item.get("guid") for item in dependencies if isinstance(item, dict)]
    if len(dependencies) != 32 or len(set(dependency_guids)) != 32:
        errors.append("dependency closure must contain 32 unique entries")
    for index, item in enumerate(dependencies):
        try:
            uuid.UUID(str(item.get("guid")))
        except (AttributeError, ValueError):
            errors.append(f"dependency {index} has an invalid GUID")
        roles = item.get("roles") if isinstance(item, dict) else None
        if not isinstance(roles, list) or not roles or any(not isinstance(role, str) or not role for role in roles):
            errors.append(f"dependency {index} has invalid roles")
    role_map = {item.get("guid"): item.get("roles", []) for item in dependencies if isinstance(item, dict)}
    if role_map.get("f46c0d0d-2c8c-4189-8893-edb74832529c") != ["hierarchy"]:
        errors.append("hierarchy dependency is missing")
    if role_map.get("560ef428-7854-4249-9466-7188a4b4ac7a") != ["clothColliderReference"]:
        errors.append("cloth collider dependency is missing")
    summary = data.get("summary", {})
    if summary != {"nodes": 108, "node_types": 7, "unique_dependencies": 32}:
        errors.append("summary mismatch")
    for field in ("animation", "entity", "world", "save"):
        if data.get("attachments", {}).get(field) is not False:
            errors.append(f"unexpected attachment: {field}")
    if data.get("result") != "animation_graph_dependency_traversal_complete":
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
        "verified_node_count": 108 if not errors else None,
        "verified_dependency_count": 32 if not errors else None,
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
