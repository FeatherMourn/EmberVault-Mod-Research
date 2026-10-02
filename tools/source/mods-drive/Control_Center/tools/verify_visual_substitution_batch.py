"""Validate a generated visual-substitution batch plan before execution."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def validate(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read plan: {exc}"]
    errors: list[str] = []
    if data.get("schema") != "control_center.visual_substitution_batch_plan.v1":
        errors.append("unsupported plan schema")
    policy = data.get("execution_policy", {})
    for key, expected in (("stable_profile_allowed", False), ("requires_fresh_eml_session", True), ("requires_screenshot_verdict", True), ("requires_cleanup_after_run", True), ("save_policy", "do-not-save-until-explicitly-approved")):
        if policy.get(key) != expected:
            errors.append(f"execution_policy.{key} must be {expected!r}")
    runs = data.get("runs")
    if not isinstance(runs, list) or not runs:
        errors.append("runs must be a non-empty list")
        return errors
    item_ids, recipe_ids, sequences = set(), set(), set()
    for index, run in enumerate(runs):
        prefix = f"runs[{index}]"
        if not isinstance(run, dict):
            errors.append(prefix + " must be an object")
            continue
        for field, seen in (("item_id", item_ids), ("recipe_id", recipe_ids), ("sequence", sequences)):
            value = run.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0 or value in seen:
                errors.append(f"{prefix}.{field} must be a unique positive integer")
            seen.add(value)
        if not isinstance(run.get("fields"), list) or not run["fields"]:
            errors.append(prefix + ".fields must be non-empty")
        if run.get("state") != "planned":
            errors.append(prefix + ".state must be planned before execution")
        for key in ("requires_screenshot_verdict", "cleanup_required", "save_requires_explicit_approval"):
            if run.get(key) is not True:
                errors.append(f"{prefix}.{key} must be true")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    errors = validate(args.plan)
    print(json.dumps({"schema": "control_center.visual_substitution_batch_verification.v1", "valid": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
