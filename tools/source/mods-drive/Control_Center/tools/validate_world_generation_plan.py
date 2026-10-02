"""Validate a research-only world-generation authoring plan."""
from __future__ import annotations
import argparse, json
from pathlib import Path

SCHEMA = "control_center.world_generation_plan.v1"
PROHIBITED = {"read-voxel-content", "write-live-world", "register-resource", "attach-resource", "write-save", "multiplayer-use"}
ALLOWED_OPS = {"map-layer", "replace-donor-reference", "preview-bounds", "record-material-intent"}

def validate(path: Path, expected_build: str | None = None) -> dict:
    errors = []
    try: data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc: return {"valid": False, "errors": [str(exc)]}
    if data.get("schema") != SCHEMA: errors.append("unsupported schema")
    if data.get("feature_state") != "research-only": errors.append("plan must be research-only")
    if expected_build is not None and data.get("game_build") != expected_build: errors.append("game build mismatch")
    if not isinstance(data.get("name"), str) or not data["name"].strip(): errors.append("name is required")
    if not isinstance(data.get("prohibited_actions"), list) or not PROHIBITED.issubset(set(data.get("prohibited_actions", []))): errors.append("safety prohibitions are incomplete")
    for index, operation in enumerate(data.get("operations", [])):
        if not isinstance(operation, dict): errors.append(f"operation {index} must be an object"); continue
        if operation.get("kind") not in ALLOWED_OPS: errors.append(f"operation {index} has an unsupported kind")
        if operation.get("approved") is not False: errors.append(f"operation {index} must not be approved")
    promotion = data.get("promotion", {})
    for key in ("runtime_payload_read", "authoring_verified", "save_verified", "multiplayer_verified"):
        if promotion.get(key) is not False: errors.append(f"promotion flag must be false: {key}")
    return {"schema": "control_center.world_generation_plan_validation.v1", "valid": not errors, "state": "research-only", "errors": errors}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("plan", type=Path); parser.add_argument("--expected-build")
    args = parser.parse_args(); result = validate(args.plan, args.expected_build); print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["valid"] else 1

if __name__ == "__main__": raise SystemExit(main())
