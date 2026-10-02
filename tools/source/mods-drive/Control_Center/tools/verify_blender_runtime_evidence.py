"""Validate runtime evidence for a Blender-generated research package."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "control_center.blender_render_model_round_trip_runtime_evidence.v1"
REQUIRED_RUNTIME = (
    "process_started",
    "loader_completed_without_panic",
    "custom_textures_registered",
    "custom_material_assigned",
    "new_item_registered",
    "new_recipe_registered",
    "catalog_entry_added",
    "custom_render_model_assigned",
)


def validate(path: Path) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "control_center.blender_runtime_evidence_verification.v1", "valid": False,
                "path": str(path), "errors": [str(exc)]}
    if data.get("schema") != SCHEMA:
        errors.append("unsupported schema")
    if not data.get("target_build"):
        errors.append("target_build is required")
    runtime = data.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("runtime must be an object")
    else:
        for key in REQUIRED_RUNTIME:
            if runtime.get(key) is not True:
                errors.append(f"runtime.{key} must be true")
    visual = data.get("visual_evidence")
    rollback = data.get("rollback")
    if not isinstance(visual, dict):
        errors.append("visual_evidence must be an object")
    if not isinstance(rollback, dict) or rollback.get("probe_removed") is not True or rollback.get("stable_profile_restored") is not True:
        errors.append("probe removal and stable profile restoration are required")
    if data.get("promotion_ready") is True and (not isinstance(visual, dict) or visual.get("catalog_visible") is not True or visual.get("placed_object_visible") is not True):
        errors.append("promotion_ready requires catalog and placed-object proof")
    return {"schema": "control_center.blender_runtime_evidence_verification.v1", "valid": not errors,
            "path": str(path), "state": data.get("state"), "promotion_ready": data.get("promotion_ready"),
            "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    result = validate(args.evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
