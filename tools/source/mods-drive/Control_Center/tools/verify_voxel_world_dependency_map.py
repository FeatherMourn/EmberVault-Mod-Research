"""Verify the build-pinned offline VoxelWorld dependency map."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def verify(path: Path) -> dict:
    errors: list[str] = []
    try: data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc: return {"valid": False, "errors": [str(exc)]}
    expected = {
        "schema": "control_center.voxel_world_dependency_map.v1",
        "read_only": True,
        "world_count": 135,
        "unique_world_guid_count": 130,
        "scene_owned_world_count": 10,
        "standalone_world_count": 125,
        "unique_material_guid_count": 198,
        "unique_content_hash_count": 19861,
        "referenced_content_bytes": 4865080612,
        "invalid_entries": [],
    }
    for key, value in expected.items():
        if data.get(key) != value: errors.append(f"field mismatch: {key}")
    if data.get("world_type_counts") != {"Fog": 5, "Solid": 130}:
        errors.append("world type counts mismatch")
    donor = next((item for item in data.get("worlds", []) if item.get("guid") == "022bd475-089a-43b8-b49a-2bcf2f0cd84f"), None)
    if donor is None or donor.get("scene_owned") is not False or donor.get("content_hash_count") != 7:
        errors.append("verified standalone donor boundary mismatch")
    if not data.get("limitations"): errors.append("limitations are missing")
    return {"schema": "control_center.voxel_world_dependency_map_verification.v1", "valid": not errors, "errors": errors}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("evidence",type=Path); args=parser.parse_args()
    result=verify(args.evidence); print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
