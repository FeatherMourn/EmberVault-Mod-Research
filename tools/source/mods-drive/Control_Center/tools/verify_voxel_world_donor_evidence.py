"""Fail-closed verifier for one bounded VoxelWorld donor payload readback."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "control_center.voxel_world_donor_evidence_verification.v1"
TYPE = "keen::VoxelWorldResource"
GUID = "022bd475-089a-43b8-b49a-2bcf2f0cd84f"


def verify(path: Path, expected_build: str, expected_api: str) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"schema": SCHEMA, "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.voxel_world_single_donor_runtime_evidence.v1":
        errors.append("unsupported evidence schema")
    if data.get("game_build") != expected_build:
        errors.append("game build mismatch")
    if data.get("loader_api_version") != expected_api:
        errors.append("loader API mismatch")
    if data.get("resource_type") != TYPE or data.get("donor_guid") != GUID or data.get("resource_part") != 0:
        errors.append("resource donor identity mismatch")
    if data.get("read_only") is not True or data.get("bounded") is not True:
        errors.append("probe was not bounded and read-only")
    lookup = data.get("resource_lookup", {})
    for field in ("ok", "found", "guid_matches"):
        if lookup.get(field) is not True:
            errors.append(f"resource lookup {field} is not verified")
    payload = data.get("payload_read", {})
    if payload.get("ok") is not True or payload.get("data_type") != "userdata":
        errors.append("typed payload readback is not verified")
    fields = data.get("fields", {})
    expected_fields = {
        "world_type": "Solid",
        "size": {"x": 256, "y": 16, "z": 256},
        "origin": {"x": 0, "y": 0, "z": 0},
        "material_count": 256,
        "default_terrain_material": 0,
        "voxel_level_count": 7,
        "level_0_tile_size": {"x": 8, "y": 8},
        "level_0_tile_count": {"x": 1, "y": 1},
        "level_0_tiles_count": 1,
        "cpu_displacement_size": 0,
        "voxel_hashes_size": 0,
    }
    for field, expected in expected_fields.items():
        if fields.get(field) != expected:
            errors.append(f"field mismatch: {field}")
    boundaries = data.get("prohibited_boundaries", {})
    for field in ("created", "registered", "mutated", "attached", "world", "save"):
        if boundaries.get(field) is not False:
            errors.append(f"prohibited boundary crossed: {field}")
    if data.get("result") != "single_voxel_world_payload_read_complete":
        errors.append("completion marker is missing")
    if data.get("current_session_errors") != []:
        errors.append("current session contains errors")
    cleanup = data.get("cleanup", {})
    for field in ("game_stopped", "probe_uninstalled", "stable_profile_restored", "isolation_ready"):
        if cleanup.get(field) is not True:
            errors.append(f"cleanup {field} is not verified")
    if cleanup.get("live_research_mod_count") != 0 or cleanup.get("live_stable_mod_count") != 1:
        errors.append("live profile isolation mismatch")
    if data.get("promotion_ready") is not False or not data.get("limitations"):
        errors.append("research-only limitation boundary is missing")
    return {
        "schema": SCHEMA,
        "valid": not errors,
        "state": "research-only",
        "promotion_ready": False,
        "verified_voxel_level_count": fields.get("voxel_level_count"),
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
