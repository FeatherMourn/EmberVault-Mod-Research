"""Verify a donor-preserving TemplateResource visual candidate."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.template_graph import TemplateGraphError, TemplateGraphPlanner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="donor TemplateResource JSON")
    parser.add_argument("candidate", type=Path, help="candidate TemplateResource JSON")
    parser.add_argument("replacement_model_guid")
    parser.add_argument("--model-component-index", type=int)
    args = parser.parse_args()
    try:
        plan = TemplateGraphPlanner().plan(
            args.source, args.replacement_model_guid, args.model_component_index
        )
        valid, unexpected = TemplateGraphPlanner.verify_candidate(plan, args.candidate)
        result = {
            "schema": "control_center.template_candidate_verification.v1",
            "valid": valid,
            "source": str(plan.source),
            "candidate": str(args.candidate.resolve()),
            "component_path": plan.component_path,
            "donor_model_guid": plan.donor_model_guid,
            "replacement_model_guid": plan.replacement_model_guid,
            "source_sha256": plan.source_sha256,
            "unexpected_differences": list(unexpected),
            "runtime_status": "research-only",
        }
    except (TemplateGraphError, OSError, ValueError) as exc:
        result = {
            "schema": "control_center.template_candidate_verification.v1",
            "valid": False,
            "error": str(exc),
            "runtime_status": "research-only",
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
