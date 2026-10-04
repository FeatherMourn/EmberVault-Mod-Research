"""Audit the durable catalog for exact and cross-build identity collisions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.catalog_store import CatalogStore
from src.identity import duplicate_groups


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=ROOT / "research/catalog.sqlite")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    store = CatalogStore(args.catalog)
    try:
        records = store.records()
    finally:
        store.close()
    report = {"schema_version": 1, "record_count": len(records),
              "exact_duplicate_groups": duplicate_groups(records),
              "cross_build_identity_groups": duplicate_groups(records, include_build=False)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"audited {len(records)} records; exact={len(report['exact_duplicate_groups'])}, cross_build={len(report['cross_build_identity_groups'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
