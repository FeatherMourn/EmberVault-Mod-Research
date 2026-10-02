"""Verify same-GUID scene-family metadata and part ranges."""
from __future__ import annotations
import argparse,json
from pathlib import Path

EXPECTED={"keen::SceneResource":[0],"keen::VoxelWorldResource":[0,1],"keen::VoxelWorldChunkResource":[],"keen::VoxelWorldFog3Resource":[0],"keen::WaterWorldResource":[0],"keen::WaterChunkResource":[0],"keen::SceneEntityChunkResource":[0,1],"keen::RenderModelChunkGridResource":[],"keen::RenderModelChunkModelResource":[0,1],"keen::FogVoxelMappingResource":[0]}

def verify(path:Path,build:str,api:str)->dict:
    errors=[]
    try:data=json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError,ValueError) as exc:return {"valid":False,"errors":[str(exc)]}
    if data.get("schema")!="control_center.scene_resource_family_metadata_runtime_evidence.v1":errors.append("unsupported evidence schema")
    if data.get("game_build")!=build:errors.append("game build mismatch")
    if data.get("loader_api_version")!=api:errors.append("loader API mismatch")
    if data.get("guid")!="36234b22-85f2-4001-ac56-002b379d0d88":errors.append("GUID mismatch")
    if data.get("read_only") is not True or data.get("metadata_only") is not True:errors.append("probe was not metadata-only and read-only")
    if data.get("families")!=EXPECTED:errors.append("family/part map mismatch")
    for field in ("payload","created","registered","mutated","attached","world","save"):
        if data.get("boundary",{}).get(field) is not False:errors.append(f"prohibited boundary crossed: {field}")
    if data.get("result")!="scene_resource_family_metadata_complete":errors.append("completion marker is missing")
    if data.get("current_session_errors")!=[]:errors.append("current session contains errors")
    for field in ("game_stopped","probe_uninstalled","stable_profile_restored","isolation_ready"):
        if data.get("cleanup",{}).get(field) is not True:errors.append(f"cleanup {field} is not verified")
    if data.get("promotion_ready") is not False or not data.get("limitations"):errors.append("research-only boundary is missing")
    return {"schema":"control_center.scene_resource_family_evidence_verification.v1","valid":not errors,"state":"research-only","promotion_ready":False,"family_count":len(data.get("families",{})),"errors":errors}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("evidence",type=Path);p.add_argument("--expected-build",required=True);p.add_argument("--expected-api",required=True);a=p.parse_args();r=verify(a.evidence,a.expected_build,a.expected_api);print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["valid"] else 1

if __name__=="__main__":raise SystemExit(main())
