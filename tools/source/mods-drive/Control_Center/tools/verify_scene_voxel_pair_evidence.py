"""Fail-closed verifier for a paired SceneResource and VoxelWorld readback."""
from __future__ import annotations
import argparse,json
from pathlib import Path

GUID="36234b22-85f2-4001-ac56-002b379d0d88"

def verify(path:Path,expected_build:str,expected_api:str)->dict:
    errors=[]
    try:data=json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError,ValueError) as exc:return {"valid":False,"errors":[str(exc)]}
    if data.get("schema")!="control_center.scene_voxel_pair_runtime_evidence.v1":errors.append("unsupported evidence schema")
    if data.get("game_build")!=expected_build:errors.append("game build mismatch")
    if data.get("loader_api_version")!=expected_api:errors.append("loader API mismatch")
    if data.get("shared_guid")!=GUID:errors.append("shared GUID mismatch")
    if data.get("read_only") is not True or data.get("paired") is not True:errors.append("probe was not paired and read-only")
    expected={
      "scene":("keen::SceneResource",0,{"nodes":5,"models":0,"lights":0,"cameras":1,"vfxs":4,"sounds":0,"entity_chunks":{"x":1,"y":1},"ibl_intensity":1.0}),
      "solid":("keen::VoxelWorldResource",0,{"world_type":"Solid","size":{"x":256,"y":0,"z":256},"fixed_material_slots":256,"voxel_levels":7,"tile_references":10,"default_material":1}),
      "fog":("keen::VoxelWorldResource",1,{"world_type":"Fog","size":{"x":256,"y":0,"z":256},"fixed_material_slots":256,"voxel_levels":7,"tile_references":10,"default_material":0}),
    }
    for label,(type_name,part,fields) in expected.items():
        row=data.get("resources",{}).get(label,{})
        if row.get("type")!=type_name or row.get("part")!=part:errors.append(f"{label} identity mismatch")
        for flag in ("lookup_ok","found","guid_matches"):
            if row.get(flag) is not True:errors.append(f"{label} {flag} is not verified")
        if row.get("payload_type")!="userdata":errors.append(f"{label} payload type mismatch")
        if row.get("fields")!=fields:errors.append(f"{label} field parity mismatch")
    relation=data.get("relationship",{})
    if relation!={"shared_guid":True,"scene_part":0,"solid_part":0,"fog_part":1,"runtime_and_offline_parity":True}:errors.append("resource relationship mismatch")
    for field in ("content","created","registered","mutated","attached","world","save"):
        if data.get("boundary",{}).get(field) is not False:errors.append(f"prohibited boundary crossed: {field}")
    if data.get("result")!="scene_voxel_pair_read_complete":errors.append("completion marker is missing")
    if data.get("current_session_errors")!=[]:errors.append("current session contains errors")
    for field in ("game_stopped","probe_uninstalled","stable_profile_restored","isolation_ready"):
        if data.get("cleanup",{}).get(field) is not True:errors.append(f"cleanup {field} is not verified")
    if data.get("promotion_ready") is not False or not data.get("limitations"):errors.append("research-only boundary is missing")
    return {"schema":"control_center.scene_voxel_pair_evidence_verification.v1","valid":not errors,"state":"research-only","promotion_ready":False,"relationship_verified":not any("relationship" in error for error in errors),"errors":errors}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("evidence",type=Path);p.add_argument("--expected-build",required=True);p.add_argument("--expected-api",required=True);a=p.parse_args();r=verify(a.evidence,a.expected_build,a.expected_api);print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["valid"] else 1

if __name__=="__main__":raise SystemExit(main())
