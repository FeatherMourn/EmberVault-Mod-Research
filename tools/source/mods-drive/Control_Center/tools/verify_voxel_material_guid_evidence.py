"""Fail-closed verifier for bounded VoxelWorld material-GUID metadata evidence."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def verify(path: Path, expected_build: str, expected_api: str) -> dict:
    errors: list[str] = []
    try: data=json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError,ValueError) as exc: return {"valid":False,"errors":[str(exc)]}
    if data.get("schema") != "control_center.voxel_material_guid_type_runtime_evidence.v1": errors.append("unsupported evidence schema")
    if data.get("game_build") != expected_build: errors.append("game build mismatch")
    if data.get("loader_api_version") != expected_api: errors.append("loader API mismatch")
    if data.get("api") != "game.assets.get_resource_metadata_by_guid": errors.append("metadata API mismatch")
    if data.get("read_only") is not True or data.get("metadata_only") is not True: errors.append("probe was not metadata-only and read-only")
    for key,value in {"sample_count":12,"resolved_guid_count":7,"resource_match_count":7,"unresolved_guid_count":5,"material_resource_type_matches":0}.items():
        if data.get(key) != value: errors.append(f"field mismatch: {key}")
    resolved=data.get("resolved",[])
    if len(resolved) != 7 or any(row.get("matches") != [{"type":"keen::VoxelWorldResource","part":0}] for row in resolved):
        errors.append("resolved identity classification mismatch")
    if len(data.get("unresolved",[])) != 5: errors.append("unresolved identity count mismatch")
    for field in ("payload","created","registered","mutated","world","save"):
        if data.get("boundary",{}).get(field) is not False: errors.append(f"prohibited boundary crossed: {field}")
    if data.get("result") != "voxel_material_metadata_complete": errors.append("completion marker is missing")
    if data.get("current_session_errors") != []: errors.append("current session contains errors")
    for field in ("game_stopped","probe_uninstalled","stable_profile_restored","isolation_ready"):
        if data.get("cleanup",{}).get(field) is not True: errors.append(f"cleanup {field} is not verified")
    if data.get("promotion_ready") is not False or not data.get("limitations"): errors.append("research-only boundary is missing")
    return {"schema":"control_center.voxel_material_guid_evidence_verification.v1","valid":not errors,"state":"research-only","promotion_ready":False,"errors":errors}


def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("evidence",type=Path);p.add_argument("--expected-build",required=True);p.add_argument("--expected-api",required=True);a=p.parse_args()
    result=verify(a.evidence,a.expected_build,a.expected_api);print(json.dumps(result,indent=2,sort_keys=True));return 0 if result["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
