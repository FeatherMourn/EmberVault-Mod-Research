"""Generate a reviewed, sanitized Web Catalog snapshot from the local catalog."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.publication import build_web_publication_from_catalog


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=ROOT / "research/catalog.sqlite")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--generated-at", required=True, help="Publication date, such as 2026-10-04")
    parser.add_argument("--reviewed-id", action="append", required=True)
    args = parser.parse_args()
    publication = build_web_publication_from_catalog(
        args.catalog, reviewed_ids=set(args.reviewed_id), generated_at=args.generated_at
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(publication, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(publication['records'])} reviewed records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
