"""Dependency-free command-line viewer for the offline Research Lab."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .catalog_store import CatalogStore
from .research_index import search
from .research_lab import (build_comparison_view, build_lab_snapshot, contradiction_review_view,
                           relationship_view, unified_review_snapshot, web_publication_preview)


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
    parser.add_argument("--report", choices=("snapshot", "relationships", "contradictions", "diff", "publication", "notebook", "unified"), default="snapshot")
    parser.add_argument("--record-id")
    parser.add_argument("--from-build")
    parser.add_argument("--to-build")
    parser.add_argument("--reviewed-id", action="append", default=[])
    parser.add_argument("--notebook", type=Path)
    args = parser.parse_args(argv)
    records = load_records(args.input)
    notebook = None
    if args.notebook:
        notebook = json.loads(args.notebook.read_text(encoding="utf-8"))
    if args.report == "relationships":
        if not args.record_id:
            parser.error("--record-id is required for relationships")
        snapshot = relationship_view(records, args.record_id)
    elif args.report == "contradictions":
        snapshot = contradiction_review_view(records, [])
    elif args.report == "diff":
        if not args.from_build or not args.to_build:
            parser.error("--from-build and --to-build are required for diff")
        snapshot = build_comparison_view(records, args.from_build, args.to_build)
    elif args.report == "publication":
        snapshot = web_publication_preview(records, set(args.reviewed_id))
    elif args.report == "notebook":
        snapshot = notebook or {"schema_version": 1, "entries": [], "read_only": True, "actions": []}
    elif args.report == "unified":
        snapshot = unified_review_snapshot(records, notebook=notebook, reviewed_ids=set(args.reviewed_id),
                                           from_build=args.from_build, to_build=args.to_build)
    else:
        snapshot = build_lab_snapshot(records, query=args.query, state=args.state, build=args.build,
                                      kind=args.kind, confidence=args.confidence,
                                      has_open_questions=True if args.open_questions else None)
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
