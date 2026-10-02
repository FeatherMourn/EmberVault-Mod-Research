"""Rank extracted visual resources by compatibility with a donor resource."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.resource_inspector import ResourceInspector


def rank(donor, candidate):
    differences = ResourceInspector().compare(donor, candidate)
    errors = sum(item.severity == "error" for item in differences)
    warnings = sum(item.severity == "warning" for item in differences)
    missing = sum(
        path not in candidate.schema for path in donor.schema
    )
    array_delta = sum(
        abs(length - candidate.arrays.get(path, length))
        for path, length in donor.arrays.items()
        if path in candidate.arrays
    )
    # Lower is better. Missing fields are weighted above array-shape warnings.
    score = errors * 10000 + missing * 100 + warnings * 10 + array_delta
    return score, errors, warnings, missing, array_delta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("donor", type=Path)
    parser.add_argument("search_root", type=Path)
    parser.add_argument("--resource-type", default="RenderModel")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")

    inspector = ResourceInspector()
    donor = inspector.inspect(args.donor, args.resource_type)
    results = []
    for path in sorted(args.search_root.rglob("*.json")):
        if path.resolve() == args.donor.resolve():
            continue
        try:
            candidate = inspector.inspect(path, args.resource_type)
        except ValueError:
            continue
        score, errors, warnings, missing, array_delta = rank(donor, candidate)
        results.append({
            "path": str(path),
            "guid": candidate.guid,
            "sha256": candidate.sha256,
            "score": score,
            "schema_errors": errors,
            "schema_warnings": warnings,
            "missing_fields": missing,
            "array_length_delta": array_delta,
            "graph_compatible": errors == 0 and missing == 0 and array_delta == 0,
        })
    results.sort(key=lambda item: (item["score"], item["path"]))
    report = {
        "schema": "control_center.visual_candidate_search.v1",
        "donor": str(args.donor),
        "search_root": str(args.search_root),
        "resource_type": args.resource_type,
        "candidate_count": len(results),
        "compatible_count": sum(item["graph_compatible"] for item in results),
        "candidates": results[: args.limit],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
