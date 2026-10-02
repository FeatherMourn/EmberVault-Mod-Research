"""Generate a fail-closed donor patch plan without writing the donor or output."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.content_patch import ContentPatchPlanner, ContentPatchError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("donor", type=Path)
    parser.add_argument("resource_type")
    parser.add_argument("changes", type=Path, help="JSON object mapping field paths to values")
    parser.add_argument("--output", type=Path, default=Path("planned-output.json"))
    args = parser.parse_args()
    try:
        changes = json.loads(args.changes.read_text(encoding="utf-8-sig"))
        plan = ContentPatchPlanner().plan(args.donor, args.output, args.resource_type, changes)
    except (OSError, ValueError, json.JSONDecodeError, ContentPatchError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "schema": "control_center.content_patch_plan.v1",
        "resource_type": plan.resource_type,
        "donor": str(plan.donor),
        "output": str(plan.output),
        "deployable": plan.deployable,
        "changes": [change.__dict__ for change in plan.changes],
        "runtime_mutation": False,
    }, indent=2, sort_keys=True))
    return 0 if plan.deployable else 2


if __name__ == "__main__":
    raise SystemExit(main())
