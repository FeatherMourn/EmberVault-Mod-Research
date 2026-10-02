"""Verify fresh localization runtime evidence without promoting UI claims."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def verify(path: Path, expected_build: str) -> dict:
    errors=[]
    try: data=json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc: return {"schema":"control_center.localization_session_verification.v1","valid":False,"errors":[str(exc)]}
    if data.get("schema") != "control_center.localization_fresh_session_evidence.v1": errors.append("unsupported schema")
    if str(data.get("build")) != expected_build: errors.append("build mismatch")
    if data.get("fresh_session_observed") is not True: errors.append("fresh session was not observed")
    for key in ("tag_registration", "localization_registration"):
        if not isinstance(data.get(key), dict) or data[key].get("ok") is not True: errors.append(f"{key} did not succeed")
    if data.get("panic_observed") is not False: errors.append("panic status is not clean")
    if data.get("probe_uninstalled") is not True or data.get("stable_profile_restored") is not True: errors.append("cleanup or restoration is incomplete")
    if data.get("ui_label_consumption_verified") is True: errors.append("session evidence overclaims UI consumption")
    gaps = []
    if data.get("catalog_label_verified") is not True:
        gaps.append("catalog label screenshot/readback")
    if data.get("item_info_label_verified") is not True:
        gaps.append("item-info label screenshot/readback")
    if data.get("recipe_label_verified") is not True:
        gaps.append("recipe label screenshot/readback")
    if data.get("placement_label_verified") is not True:
        gaps.append("placement label screenshot/readback")
    if data.get("state") == "verified" and gaps:
        errors.append("verified state is not allowed while localization UI gaps remain")
    return {"schema":"control_center.localization_session_verification.v1","valid":not errors,
            "errors":errors,"state":data.get("state"),"promotion_ready":not gaps and not errors,
            "evidence_gaps":gaps}

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("evidence",type=Path); parser.add_argument("--expected-build",required=True); args=parser.parse_args()
    result=verify(args.evidence,args.expected_build); print(json.dumps(result,indent=2)); return 0 if result["valid"] else 1
if __name__ == "__main__": raise SystemExit(main())
