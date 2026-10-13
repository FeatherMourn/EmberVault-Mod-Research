"""Dependency-free command-line viewer for the offline Research Lab."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .catalog_store import CatalogStore
from .research_index import search
from .research_lab import build_lab_snapshot


def load_records(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if source.suffix == ".sqlite":
        store = CatalogStore(source)
        try:
            return store.records()
        finally:
            store.close()
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    records = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("research input must contain a records list")
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="SQLite catalog or JSON records file")
    parser.add_argument("--query", default="")
    parser.add_argument("--state")
    parser.add_argument("--build")
    parser.add_argument("--kind")
    parser.add_argument("--confidence")
    parser.add_argument("--open-questions", action="store_true")
    args = parser.parse_args(argv)
    records = load_records(args.input)
    snapshot = build_lab_snapshot(records, query=args.query, state=args.state, build=args.build,
                                  kind=args.kind, confidence=args.confidence,
                                  has_open_questions=True if args.open_questions else None)
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
