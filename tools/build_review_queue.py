"""Write a deterministic evidence-gap review queue from the durable catalog."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.catalog_store import CatalogStore
from src.review_queue import build_review_queue


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=ROOT / "research/catalog.sqlite")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    store = CatalogStore(args.catalog)
    try:
        queue = build_review_queue(store.records(), store.unresolved_contradictions())
    finally:
        store.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(queue['records'])} evidence-gap records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
