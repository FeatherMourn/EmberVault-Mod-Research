"""Create a read-only visual-dependency inventory for a KFC resource."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.resource_inspector import ResourceInspector


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resource", type=Path)
    parser.add_argument("--resource-type", default=None)
    parser.add_argument("--candidate", type=Path, help="optional candidate resource for a substitution plan")
    args = parser.parse_args()
    inspector = ResourceInspector()
    record = inspector.inspect(args.resource, args.resource_type)
    report = {
        "schema": "control_center.visual_dependency_inventory.v1",
        "resource_type": record.resource_type,
        "resource": str(record.path),
        "guid": record.guid,
        "sha256": record.sha256,
        "references": inspector.visual_references(record),
        "runtime_substitution_verified": False,
    }
    if args.candidate:
        candidate = inspector.inspect(args.candidate, args.resource_type)
        report["candidate"] = str(candidate.path)
        report["substitution_plan"] = inspector.visual_substitution_plan(record, candidate)
        schema_differences = inspector.compare(record, candidate)
        report["schema_differences"] = [item.__dict__ for item in schema_differences]
        states = [item["state"] for item in report["substitution_plan"]]
        report["candidate_graph_complete"] = (
            "missing_in_candidate" not in states and
            not any(item.severity == "error" for item in schema_differences)
        )
        report["substitution_summary"] = {
            "unchanged": states.count("unchanged"),
            "candidate_reference": states.count("candidate_reference"),
            "new_candidate_reference": states.count("new_candidate_reference"),
            "missing_in_candidate": states.count("missing_in_candidate"),
        }
        report["runtime_substitution_verified"] = False
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.candidate and not report["candidate_graph_complete"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
