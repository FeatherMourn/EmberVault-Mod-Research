"""Explain module dependencies, conflicts, and load order without installing anything."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.platform_services import ModuleGraphService


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modules", type=Path, help="directory containing module folders")
    parser.add_argument("--enabled", nargs="*", help="optional enabled module IDs")
    parser.add_argument("--strict-metadata", action="store_true",
                        help="fail the graph audit for modules missing valid maturity metadata")
    args = parser.parse_args()
    service = ModuleGraphService(args.modules)
    graph = service.build(
        set(args.enabled) if args.enabled is not None else None,
        strict_metadata=args.strict_metadata,
    )
    print(json.dumps({
        "schema": "control_center.module_graph_report.v1",
        "load_order": graph.order,
        "issues": [issue.__dict__ for issue in graph.issues],
        "strict_metadata": args.strict_metadata,
        "modules": service.explain(graph),
        "runtime_mutation": False,
    }, indent=2, sort_keys=True))
    return 2 if args.strict_metadata and graph.issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
