"""Write a read-only build comparison from the durable catalog."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.build_diff import diff_builds
from src.catalog_store import CatalogStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("from_build")
    parser.add_argument("to_build")
    parser.add_argument("--catalog", type=Path, default=ROOT / "research/catalog.sqlite")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    store = CatalogStore(args.catalog)
    try:
        result = diff_builds(store.records(), args.from_build, args.to_build)
    finally:
        store.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"build diff: added={len(result['added'])}, removed={len(result['removed'])}, changed={len(result['changed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
