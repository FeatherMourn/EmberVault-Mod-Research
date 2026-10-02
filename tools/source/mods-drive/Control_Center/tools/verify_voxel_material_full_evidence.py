"""Verify complete metadata classification of one 198-entry VoxelWorld table."""
from __future__ import annotations
import argparse, json
from pathlib import Path

EXPECTED_HASHES={
    "algorithm":"sha256-sorted-lowercase-guid-lines",
    "input":"659d13b292a3ead67aa8d84ee02b39a1d91142a9586b617b1614ba09fa4a0dfd",
    "resolved":"f12013e55b7e5157d0a90a1056d7e2bd45e0cff5a41bae72b09d15ec9f214f61",
    "unresolved":"16e5d818683644671fbff19211ac03fb1aeb3b9996c757aa380a305b2cc02f9c",
}

def verify(path:Path,expected_build:str,expected_api:str)->dict:
    errors=[]
    try:data=json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError,ValueError) as exc:return {"valid":False,"errors":[str(exc)]}
    if data.get("schema")!="control_center.voxel_material_full_metadata_runtime_evidence.v1":errors.append("unsupported evidence schema")
    if data.get("game_build")!=expected_build:errors.append("game build mismatch")
    if data.get("loader_api_version")!=expected_api:errors.append("loader API mismatch")
    if data.get("read_only") is not True or data.get("metadata_only") is not True:errors.append("probe was not metadata-only and read-only")
    for key,value in {"input_guid_count":198,"resolved_guid_count":125,"unresolved_guid_count":73,"resource_match_count":125,"material_resource_type_matches":0}.items():
        if data.get(key)!=value:errors.append(f"field mismatch: {key}")
    if data.get("resolved_guid_count",0)+data.get("unresolved_guid_count",0)!=data.get("input_guid_count"):
        errors.append("classification does not cover every input GUID")
    if data.get("resource_type_counts")!={"keen::VoxelWorldResource":125}:errors.append("resource type classification mismatch")
    if data.get("identity_hashes")!=EXPECTED_HASHES:errors.append("identity-set hash mismatch")
    correlation=data.get("archive_correlation",{})
    if correlation.get("standalone_voxel_world_count")!=125 or correlation.get("resolved_entries_equal_standalone_world_count") is not True:errors.append("archive correlation mismatch")
    if correlation.get("semantic_role_verified") is not False:errors.append("semantic role is overclaimed")
    for field in ("payload","created","registered","mutated","world","save"):
        if data.get("boundary",{}).get(field) is not False:errors.append(f"prohibited boundary crossed: {field}")
    if data.get("result")!="voxel_material_full_metadata_complete":errors.append("completion marker is missing")
    if data.get("current_session_errors")!=[]:errors.append("current session contains errors")
    for field in ("game_stopped","probe_uninstalled","stable_profile_restored","isolation_ready"):
        if data.get("cleanup",{}).get(field) is not True:errors.append(f"cleanup {field} is not verified")
    if data.get("promotion_ready") is not False or not data.get("limitations"):errors.append("research-only boundary is missing")
    return {"schema":"control_center.voxel_material_full_evidence_verification.v1","valid":not errors,"state":"research-only","promotion_ready":False,"classified_guid_count":data.get("input_guid_count"),"errors":errors}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("evidence",type=Path);p.add_argument("--expected-build",required=True);p.add_argument("--expected-api",required=True);a=p.parse_args();r=verify(a.evidence,a.expected_build,a.expected_api);print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["valid"] else 1

if __name__=="__main__":raise SystemExit(main())
