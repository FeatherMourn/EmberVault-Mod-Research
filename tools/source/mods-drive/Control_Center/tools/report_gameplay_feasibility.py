"""Export the current research-only gameplay feasibility matrix."""
from __future__ import annotations

import json
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gameplay_feasibility import GameplayFeasibilityPlanner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interaction-guid")
    parser.add_argument("--interaction-key")
    parser.add_argument("--expected-effect", default="")
    parser.add_argument("--builder-item-id", type=int)
    parser.add_argument("--builder-plan", default="")
    parser.add_argument("--output", type=Path, help="also save the JSON feasibility report")
    args = parser.parse_args()
    assessments = GameplayFeasibilityPlanner().all_assessments()
    report = {
        "schema": "control_center.gameplay_feasibility.v1",
        "assessments": [
            {"area": item.area.value, "state": item.state,
             "blockers": list(item.blockers), "next_probe": item.next_probe}
            for item in assessments
        ],
        "runtime_mutation": False,
    }
    if bool(args.interaction_guid) != bool(args.interaction_key):
        parser.error("--interaction-guid and --interaction-key must be supplied together")
    if args.interaction_guid:
        report["interaction_probe"] = GameplayFeasibilityPlanner.interaction_probe_spec(
            args.interaction_guid, args.interaction_key, args.expected_effect
        )
    if args.builder_item_id is not None:
        report["builder_placement_probe"] = GameplayFeasibilityPlanner.builder_placement_spec(
            args.builder_item_id, args.builder_plan
        )
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
