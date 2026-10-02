"""Create a deterministic, disposable run plan from a preview probe matrix."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from tools.validate_catalog_preview_matrix import validate
except ModuleNotFoundError:  # direct execution from the tools directory
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.validate_catalog_preview_matrix import validate


def build_plan(matrix_path: Path, run_label: str) -> dict:
    errors = validate(matrix_path)
    if errors:
        raise ValueError("invalid matrix: " + "; ".join(errors))
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    candidates = matrix["candidates"]
    seed = hashlib.sha256(matrix_path.read_bytes()).hexdigest()[:12]
    runs = []
    for index, candidate in enumerate(candidates, 1):
        identity = 3_900_000_000 + (int(seed[:6], 16) % 90_000_000) + index * 2
        runs.append({
            "sequence": index,
            "candidate_id": candidate["id"],
            "item_id": identity,
            "recipe_id": identity + 1,
            "question": candidate["question"],
            "item_fields": candidate.get("item_fields", []),
            "clear_fields": candidate.get("clear_fields", []),
            "preserve_fields": candidate.get("preserve_fields", []),
            "ui_fields": candidate.get("ui_fields", []),
            "schema_paths": candidate.get("schema_paths", []),
            "state": candidate["state"],
            "requires_screenshot_verdict": True,
            "cleanup_required": True,
        })
    return {
        "schema": "control_center.catalog_preview_batch_plan.v1",
        "run_label": run_label,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "matrix": str(matrix_path.resolve()),
        "matrix_sha256_prefix": seed,
        "compatible_game_build": matrix["compatible_game_build"],
        "execution_policy": {
            "stable_profile_allowed": False,
            "one_fresh_eml_session_per_candidate": True,
            "stop_on_panic": True,
            "restore_profile_after_each_candidate": True,
            "uninstall_probe_after_each_candidate": True,
        },
        "runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--label", default="catalog-preview-batch")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        plan = build_plan(args.matrix, args.label)
    except ValueError as exc:
        parser.error(str(exc))
    rendered = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
