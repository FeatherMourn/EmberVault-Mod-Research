"""Validate a catalog-preview research matrix before a probe is staged."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = {
    "schema",
    "compatible_game_build",
    "safety",
    "baseline",
    "candidates",
    "verdicts",
}


def validate(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read JSON: {exc}"]
    errors: list[str] = []
    missing = sorted(REQUIRED - data.keys()) if isinstance(data, dict) else sorted(REQUIRED)
    if missing:
        errors.append("missing top-level fields: " + ", ".join(missing))
        return errors
    if data["schema"] != "control_center.catalog_preview_probe_matrix.v1":
        errors.append("unsupported schema")
    safety = data["safety"]
    for key, expected in (("feature_state", "research-only"), ("stable_profile_allowed", False), ("requires_fresh_eml_session", True), ("requires_screenshot_verdict", True), ("requires_cleanup_after_run", True)):
        if safety.get(key) != expected:
            errors.append(f"safety.{key} must be {expected!r}")
    candidates = data["candidates"]
    if not isinstance(candidates, list) or not candidates:
        errors.append("candidates must be a non-empty list")
    else:
        ids: set[str] = set()
        for index, candidate in enumerate(candidates):
            prefix = f"candidates[{index}]"
            if not isinstance(candidate, dict):
                errors.append(prefix + " must be an object")
                continue
            candidate_id = candidate.get("id")
            if not isinstance(candidate_id, str) or not candidate_id:
                errors.append(prefix + ".id must be a non-empty string")
            elif candidate_id in ids:
                errors.append(prefix + ".id is duplicated")
            else:
                ids.add(candidate_id)
            if candidate.get("state") not in {"planned", "complete", "blocked"}:
                errors.append(prefix + ".state must be planned, complete, or blocked")
            if not candidate.get("question"):
                errors.append(prefix + ".question is required")
    if not isinstance(data["verdicts"], list) or not data["verdicts"]:
        errors.append("verdicts must be a non-empty list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    args = parser.parse_args()
    errors = validate(args.matrix)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
