"""Verify bounded Hunter idle graph-edit evidence without overclaiming behavior."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SCHEMA = "control_center.animation_graph_edit_evidence_verification.v1"

def verify(path: Path, expected_build: str, expected_api: str) -> dict:
    errors: list[str] = []
    try: data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc: return {"schema": SCHEMA, "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.animation_graph_idle_variant_runtime_evidence.v1": errors.append("unsupported evidence schema")
    if data.get("game_build") != expected_build: errors.append("game build mismatch")
    if data.get("loader_api_version") != expected_api: errors.append("loader API mismatch")
    expected_edit = {"state": "idle", "state_id": 2226547610, "before_pose": 2585692075, "after_pose": 3890759935, "target_state": "idle_Var_02", "same_graph_existing_pose": True}
    if data.get("graph_edit") != expected_edit: errors.append("bounded graph edit mismatch")
    expected_attachment = {"owner": "NPC_Workshop_Hunter01", "field": "uiRendering.animationGraph2", "before": "0022fed6-0380-4125-be31-ba8b5fdcbfcd", "after": "e24552b9-ccbc-4d4a-a922-939381658b37", "verified": True}
    if data.get("attachment") != expected_attachment: errors.append("owner attachment mismatch")
    if data.get("donor_preserved") is not True: errors.append("donor preservation is not verified")
    if data.get("prohibited_boundaries") != {"template": False, "entity": False, "world": False, "save": False, "animation_payload": False}: errors.append("prohibited boundary was crossed")
    if data.get("visible_behavior_observed") is not False: errors.append("unsubstantiated visible behavior claim")
    if data.get("result") != "animation_graph_idle_variant_attached": errors.append("completion marker is missing")
    if data.get("current_session_errors") != []: errors.append("current session contains errors")
    for field in ("game_stopped", "probe_uninstalled", "stable_profile_restored", "isolation_ready"):
        if data.get("cleanup", {}).get(field) is not True: errors.append(f"cleanup {field} is not verified")
    if not data.get("limitations"): errors.append("limitations must remain documented")
    return {"schema": SCHEMA, "valid": not errors, "state": "research-only", "promotion_ready": False, "structural_edit_verified": not errors, "visible_behavior_verified": False, "errors": errors}

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("evidence",type=Path);parser.add_argument("--expected-build",required=True);parser.add_argument("--expected-api",required=True)
    args=parser.parse_args();result=verify(args.evidence,args.expected_build,args.expected_api);print(json.dumps(result,indent=2,sort_keys=True));return 0 if result["valid"] else 1

if __name__ == "__main__": raise SystemExit(main())
