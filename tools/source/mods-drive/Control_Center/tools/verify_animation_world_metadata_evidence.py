"""Verify bounded animation/world metadata evidence without promoting behavior."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "control_center.animation_world_metadata_evidence_verification.v1"
REQUIRED = {
    "keen::anim_graph::runtime_graph::AnimationGraphResource2_0": 1,
    "keen::actor::ActorSequenceResource": 1,
    "keen::VoxelWorldResource": 1,
    "keen::VoxelWorldChunkResource": 0,
    "keen::WaterWorldResource": 1,
    "keen::WorldMaterialBlending2Resource": 1,
    "keen::SimpleWorldMaterialResource": 1,
    "keen::WorldKnowledgeObjectResource": 0,
}


def verify(path: Path, expected_build: str, expected_api: str) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"schema": SCHEMA, "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.animation_world_metadata_runtime_evidence.v1":
        errors.append("unsupported evidence schema")
    if data.get("game_build") != expected_build:
        errors.append("game build mismatch")
    if data.get("loader_api_version") != expected_api:
        errors.append("loader API mismatch")
    if data.get("read_only") is not True or data.get("metadata_only") is not True:
        errors.append("probe was not metadata-only and read-only")
    limit = data.get("per_type_limit")
    if not isinstance(limit, int) or limit < 1 or limit > 256:
        errors.append("per-type limit must be bounded between 1 and 256")
    families = data.get("resource_families", {})
    for family, minimum in REQUIRED.items():
        row = families.get(family)
        if not isinstance(row, dict):
            errors.append(f"missing family: {family}")
            continue
        count = row.get("count")
        if not isinstance(count, int) or count < minimum:
            errors.append(f"invalid count for {family}")
        if count and not row.get("first_guid"):
            errors.append(f"missing first GUID for {family}")
        if isinstance(limit, int) and count == limit and row.get("limited") is not True:
            errors.append(f"bounded result is not marked limited for {family}")
    if data.get("result") != "animation_world_metadata_inventory_complete":
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
        "family_count": len(families) if isinstance(families, dict) else 0,
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
