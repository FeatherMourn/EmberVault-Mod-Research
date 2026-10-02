"""Validate typed item-color-combination runtime evidence without overclaiming visuals."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "control_center.typed_color_combination_runtime_evidence.v1"

def _build_id(value: object) -> str | None:
    """Normalize a full EML build string to its stable numeric prefix."""
    if value is None:
        return None
    text = str(value).strip()
    return text.split("|", 1)[0].strip() or None


def verify(path: Path, expected_build: str) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "control_center.typed_color_combination_evidence_verification.v1", "valid": False, "errors": [str(exc)]}
    if data.get("schema") != SCHEMA:
        errors.append("unsupported evidence schema")
    if _build_id(data.get("target_build")) != _build_id(expected_build):
        errors.append("target build mismatch")
    runtime = data.get("runtime", {})
    for key in ("fresh_eml_session", "probe_loaded", "item_color_combination_packed_assignment", "clone_registered", "clone_discovered", "probe_completed_without_panic"):
        if runtime.get(key) is not True:
            errors.append(f"runtime evidence missing or false: {key}")
    assignment = runtime.get("assignment", {})
    if assignment.get("isSet") is not True:
        errors.append("typed color assignment must set isSet=true")
    for channel in ("color0", "color1", "color2"):
        value = assignment.get(channel)
        if not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
            errors.append(f"invalid packed color channel: {channel}")
    visuals = data.get("visual_evidence", {})
    if visuals.get("catalog_tile_visible") is True or visuals.get("placed_object_visible") is True:
        errors.append("this evidence record must not claim visible recoloring")
    cleanup = data.get("cleanup", {})
    for key in ("probe_removed", "game_stopped", "live_installation_touched"):
        expected = False if key == "live_installation_touched" else True
        if cleanup.get(key) is not expected:
            errors.append(f"cleanup invariant failed: {key}")
    if data.get("state") != "research-only" or data.get("promotion_ready") is not False:
        errors.append("typed assignment evidence must remain research-only")
    return {
        "schema": "control_center.typed_color_combination_evidence_verification.v1",
        "valid": not errors,
        "state": data.get("state"),
        "promotion_ready": False,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-build", required=True)
    args = parser.parse_args()
    result = verify(args.evidence, args.expected_build)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
