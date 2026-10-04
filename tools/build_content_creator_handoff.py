"""Write a read-only Content Creator handoff from the durable research catalog."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.catalog_store import CatalogStore
from src.research_index import content_creator_handoff


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=ROOT / "research/catalog.sqlite")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    store = CatalogStore(args.catalog)
    try:
        handoff = content_creator_handoff(store.records(), contradictions=store.all_contradictions())
    finally:
        store.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(handoff['records'])} design-only handoff records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
