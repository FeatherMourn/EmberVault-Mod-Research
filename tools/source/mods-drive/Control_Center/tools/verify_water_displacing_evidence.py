"""Fail-closed verifier for a bounded WaterDisplacingResource read."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def verify(path: Path, build: str, api: str) -> dict:
    errors=[]
    try: data=json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError,ValueError) as exc: return {"valid":False,"errors":[str(exc)]}
    if data.get("schema")!="control_center.water_displacing_runtime_evidence.v1": errors.append("unsupported evidence schema")
    if data.get("game_build")!=build: errors.append("game build mismatch")
    if data.get("loader_api_version")!=api: errors.append("loader API mismatch")
    if data.get("resource_type")!="keen::WaterDisplacingResource" or data.get("part")!=0: errors.append("resource identity mismatch")
    if data.get("guid")!="36234b22-85f2-4001-ac56-002b379d0d88": errors.append("GUID mismatch")
    if data.get("read_only") is not True or data.get("bounded") is not True: errors.append("probe boundary mismatch")
    if data.get("resource_lookup")!={"ok":True,"found":True,"guid_matches":True}: errors.append("lookup mismatch")
    if data.get("payload_read")!={"ok":True,"data_type":"userdata"}: errors.append("payload mismatch")
    if data.get("fields")!={"hash_count":16,"entry_size":16,"first_hash0":3235778711,"last_hash2":3527865979}: errors.append("field parity mismatch")
    if data.get("offline_runtime_parity") is not True: errors.append("offline/runtime parity missing")
    for field in ("hash_content","created","registered","mutated","attached","world","save"):
        if data.get("boundary",{}).get(field) is not False: errors.append(f"prohibited boundary crossed: {field}")
    if data.get("result")!="water_displacing_payload_read_complete": errors.append("completion marker missing")
    if data.get("current_session_errors")!=[]: errors.append("current session errors")
    for field in ("game_stopped","probe_uninstalled","stable_profile_restored","isolation_ready"):
        if data.get("cleanup",{}).get(field) is not True: errors.append(f"cleanup {field} is not verified")
    if data.get("promotion_ready") is not False or not data.get("limitations"): errors.append("research-only boundary missing")
    return {"schema":"control_center.water_displacing_evidence_verification.v1","valid":not errors,"state":"research-only","promotion_ready":False,"errors":errors}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("evidence",type=Path); p.add_argument("--expected-build",required=True); p.add_argument("--expected-api",required=True); a=p.parse_args(); r=verify(a.evidence,a.expected_build,a.expected_api); print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r["valid"] else 1
if __name__=="__main__": raise SystemExit(main())
