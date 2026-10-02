"""Verify fresh visual-substitution runtime evidence without overclaiming rendering."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def _build_id(value: object) -> str | None:
    """Normalize a full EML build string to its stable numeric prefix."""
    if value is None:
        return None
    text = str(value).strip()
    return text.split("|", 1)[0].strip() or None

def verify(path: Path, expected_build: str) -> dict:
    errors=[]
    try: data=json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc: return {"schema":"control_center.visual_substitution_session_verification.v1","valid":False,"errors":[str(exc)]}
    if data.get("schema") != "control_center.registered_visual_substitution_fresh_evidence.v1": errors.append("unsupported schema")
    if _build_id(data.get("build")) != _build_id(expected_build): errors.append("build mismatch")
    if data.get("fresh_session_observed") is not True: errors.append("fresh session was not observed")
    if data.get("visual_assignment",{}).get("ok") is not True: errors.append("visual assignment did not succeed")
    assignment_only = data.get("evidence_scope") == "assignment_only"
    if not assignment_only and (data.get("item_registered") is not True or data.get("recipe_registered") is not True):
        errors.append("clone registration incomplete")
    if assignment_only and not data.get("assignment_boundary"):
        errors.append("assignment-only evidence must state its boundary")
    if data.get("panic_observed") is not False: errors.append("panic status is not clean")
    if data.get("probe_uninstalled") is not True or data.get("stable_profile_restored") is not True: errors.append("cleanup or restoration is incomplete")
    if not isinstance(data.get("limitations"), list) or not data.get("limitations"):
        errors.append("limitations must explicitly record unverified visual or persistence claims")
    visual_evidence = data.get("visual_evidence")
    if visual_evidence is not None:
        if not isinstance(visual_evidence, dict):
            errors.append("visual_evidence must be an object")
        else:
            root = Path(__file__).resolve().parents[1]
            for key in ("catalog_screenshot", "placed_object_screenshot"):
                screenshot = visual_evidence.get(key)
                if not isinstance(screenshot, str) or not screenshot:
                    errors.append(f"visual evidence missing {key}")
                    continue
                screenshot_path = Path(screenshot)
                if not screenshot_path.is_absolute():
                    screenshot_path = root / screenshot_path
                if not screenshot_path.is_file():
                    errors.append(f"visual evidence file missing: {key}")
    if data.get("world_reached") is True:
        world_screenshot = data.get("world_screenshot")
        if not isinstance(world_screenshot, str) or not world_screenshot:
            errors.append("world_reached requires a durable world_screenshot")
        else:
            screenshot_path = Path(world_screenshot)
            if not screenshot_path.is_absolute():
                screenshot_path = Path(__file__).resolve().parents[1] / screenshot_path
            if not screenshot_path.is_file():
                errors.append("world screenshot file missing")
        if not isinstance(data.get("world_screenshot_verdict"), str) or not data.get("world_screenshot_verdict"):
            errors.append("world_reached requires an explicit screenshot verdict")
    if data.get("state") == "verified" and not isinstance(visual_evidence, dict):
        errors.append("verified visual substitution requires durable visual_evidence")
    gaps = []
    if data.get("placed_object_visual_verified") is not True:
        gaps.append("human-visible placed-object replacement screenshot")
    if data.get("save_persistence_verified") is not True:
        gaps.append("fresh-launch save-persistence evidence")
    if data.get("state") == "verified" and gaps:
        errors.append("verified state is not allowed while visual-substitution evidence gaps remain")
    return {"schema":"control_center.visual_substitution_session_verification.v1",
            "valid":not errors,"errors":errors,"state":data.get("state"),
            "promotion_ready": not assignment_only and not gaps and not errors,
            "evidence_gaps": gaps}

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("evidence",type=Path); parser.add_argument("--expected-build",required=True); args=parser.parse_args(); result=verify(args.evidence,args.expected_build); print(json.dumps(result,indent=2)); return 0 if result["valid"] else 1
if __name__=="__main__": raise SystemExit(main())
