"""Verify a catalog-preview batch plan before any runtime installation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.validate_catalog_preview_matrix import validate
except ModuleNotFoundError:  # direct execution from the tools directory
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.validate_catalog_preview_matrix import validate


REQUIRED_POLICY = {
    "stable_profile_allowed": False,
    "one_fresh_eml_session_per_candidate": True,
    "stop_on_panic": True,
    "restore_profile_after_each_candidate": True,
    "uninstall_probe_after_each_candidate": True,
}


def verify(plan_path: Path, matrix_path: Path, expected_build: str | None = None) -> dict:
    errors: list[str] = []
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "control_center.catalog_preview_batch_verification.v1", "valid": False, "errors": [str(exc)]}

    matrix_errors = validate(matrix_path)
    errors.extend(f"matrix: {error}" for error in matrix_errors)
    try:
        matrix_bytes = matrix_path.read_bytes()
        matrix = json.loads(matrix_bytes.decode("utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"matrix unreadable: {exc}")
        matrix = {}

    expected_hash = hashlib.sha256(matrix_path.read_bytes()).hexdigest()[:12] if matrix_path.exists() else ""
    if plan.get("schema") != "control_center.catalog_preview_batch_plan.v1":
        errors.append("unsupported or missing plan schema")
    if plan.get("matrix_sha256_prefix") != expected_hash:
        errors.append("plan matrix hash does not match the current matrix")
    if expected_build and plan.get("compatible_game_build") != expected_build:
        errors.append("plan build does not match the requested game build")
    if plan.get("compatible_game_build") != matrix.get("compatible_game_build"):
        errors.append("plan and matrix build pins differ")
    policy = plan.get("execution_policy", {})
    for key, value in REQUIRED_POLICY.items():
        if policy.get(key) != value:
            errors.append(f"unsafe execution policy: {key} must be {value!r}")

    runs = plan.get("runs", [])
    if not isinstance(runs, list) or not runs:
        errors.append("plan must contain at least one run")
        runs = []
    ids = [value for run in runs if isinstance(run, dict) for value in (run.get("item_id"), run.get("recipe_id"))]
    if len(ids) != len(set(ids)):
        errors.append("item and recipe IDs must be globally unique")
    if any(not isinstance(run, dict) or run.get("state") != "planned" for run in runs):
        errors.append("every batch run must be in planned state before installation")
    if any(not isinstance(run, dict) or not run.get("cleanup_required") or not run.get("requires_screenshot_verdict") for run in runs):
        errors.append("every run must require cleanup and screenshot evidence")

    return {
        "schema": "control_center.catalog_preview_batch_verification.v1",
        "valid": not errors,
        "plan": str(plan_path.resolve()),
        "matrix": str(matrix_path.resolve()),
        "run_count": len(runs),
        "compatible_game_build": plan.get("compatible_game_build"),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--expected-build")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.plan, args.matrix, args.expected_build)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
