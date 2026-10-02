"""Report offline build-plan materials and inventory shortages."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.builder_catalog import BuilderCatalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path, help="builder catalog JSON")
    parser.add_argument("plan", type=Path, help="saved build-plan JSON")
    parser.add_argument("--inventory", type=Path, help="JSON object mapping material names to quantities")
    args = parser.parse_args()
    catalog = BuilderCatalog.from_json_file(args.catalog)
    build_plan = catalog.load_build_plan(args.plan)
    available = {}
    if args.inventory:
        available = json.loads(args.inventory.read_text(encoding="utf-8"))
    report = {
        "schema": "control_center.build_plan_report.v1",
        "name": build_plan.name,
        "items": build_plan.item_breakdown(catalog),
        "required_materials": build_plan.materials(catalog),
        "shortages": build_plan.shortages(catalog, available),
        "runtime_mutation": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
