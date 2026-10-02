"""Create a deterministic, disposable plan for visual-substitution probes."""
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from tools.verify_visual_substitution_matrix import validate
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.verify_visual_substitution_matrix import validate

def build_plan(matrix_path: Path, run_label: str) -> dict:
    errors = validate(matrix_path)
    if errors:
        raise ValueError("invalid matrix: " + "; ".join(errors))
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    seed = hashlib.sha256(matrix_path.read_bytes()).hexdigest()[:12]
    base = 3_910_000_000 + int(seed[:6], 16) % 80_000_000
    runs = []
    for index, candidate in enumerate(matrix["candidates"], 1):
        item_id = base + index * 2
        runs.append({
            "sequence": index,
            "candidate_id": candidate["id"],
            "item_id": item_id,
            "recipe_id": item_id + 1,
            "fields": candidate["fields"],
            "question": candidate["question"],
            "state": "planned",
            "requires_screenshot_verdict": True,
            "cleanup_required": True,
            "save_requires_explicit_approval": True,
        })
    return {
        "schema": "control_center.visual_substitution_batch_plan.v1",
        "run_label": run_label,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "matrix": str(matrix_path.resolve()),
        "matrix_sha256_prefix": seed,
        "compatible_game_build": matrix["compatible_game_build"],
        "execution_policy": matrix["safety"],
        "runs": runs,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--label", default="visual-substitution-batch")
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
