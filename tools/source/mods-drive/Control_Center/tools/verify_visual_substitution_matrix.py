"""Validate the isolated visual-substitution research matrix."""
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED = {"schema", "compatible_game_build", "safety", "baseline", "candidates", "verdicts"}

def validate(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read JSON: {exc}"]
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["matrix must be an object"]
    errors.extend(f"missing top-level field: {key}" for key in sorted(REQUIRED - data.keys()))
    if data.get("schema") != "control_center.visual_substitution_probe_matrix.v1":
        errors.append("unsupported schema")
    safety = data.get("safety", {})
    for key, expected in (("feature_state", "research-only"), ("stable_profile_allowed", False), ("requires_fresh_eml_session", True), ("requires_screenshot_verdict", True), ("requires_cleanup_after_run", True), ("save_policy", "do-not-save-until-explicitly-approved")):
        if safety.get(key) != expected:
            errors.append(f"safety.{key} must be {expected!r}")
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        errors.append("candidates must be a non-empty list")
    else:
        seen: set[str] = set()
        for index, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                errors.append(f"candidates[{index}] must be an object")
                continue
            identifier = candidate.get("id")
            if not isinstance(identifier, str) or not identifier or identifier in seen:
                errors.append(f"candidates[{index}].id must be unique and non-empty")
            seen.add(str(identifier))
            if not isinstance(candidate.get("fields"), list) or not candidate["fields"]:
                errors.append(f"candidates[{index}].fields must be non-empty")
            if not str(candidate.get("question", "")).strip():
                errors.append(f"candidates[{index}].question is required")
    if not isinstance(data.get("verdicts"), list) or not data["verdicts"]:
        errors.append("verdicts must be a non-empty list")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    args = parser.parse_args()
    errors = validate(args.matrix)
    print(json.dumps({"schema": "control_center.visual_substitution_matrix_verification.v1", "valid": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
