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
from .review_queue import compare_review_priority, review_priority_summary
from .research_lab_export import (create_snapshot_bundle, prune_snapshot_bundles,
                                  recover_snapshot_bundle, verify_snapshot_bundle)


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
    parser.add_argument("input", type=Path, nargs="?", help="SQLite catalog or JSON records file")
    parser.add_argument("--query", default="")
    parser.add_argument("--state")
    parser.add_argument("--build")
    parser.add_argument("--kind")
    parser.add_argument("--confidence")
    parser.add_argument("--open-questions", action="store_true")
    parser.add_argument("--high-priority-review", action="store_true")
    parser.add_argument("--report", choices=("snapshot", "relationships", "contradictions", "review-priority", "review-diff", "diff", "publication", "notebook", "unified"), default="snapshot")
    parser.add_argument("--record-id")
    parser.add_argument("--from-build")
    parser.add_argument("--to-build")
    parser.add_argument("--reviewed-id", action="append", default=[])
    parser.add_argument("--notebook", type=Path)
    parser.add_argument("--create-bundle", type=Path)
    parser.add_argument("--verify-bundle", type=Path)
    parser.add_argument("--recover-bundle", type=Path)
    parser.add_argument("--recovery-output", type=Path)
    parser.add_argument("--prune-bundles", type=Path)
    parser.add_argument("--keep", type=int, default=5)
    args = parser.parse_args(argv)
    if sum(bool(value) for value in (args.create_bundle, args.verify_bundle, args.recover_bundle, args.prune_bundles)) > 1:
        parser.error("choose only one bundle operation")
    if args.prune_bundles:
        print(json.dumps(prune_snapshot_bundles(args.prune_bundles, keep=args.keep), indent=2, sort_keys=True))
        return 0
    if args.recover_bundle:
        if not args.recovery_output:
            parser.error("--recovery-output is required for --recover-bundle")
        print(json.dumps(recover_snapshot_bundle(args.recover_bundle, args.recovery_output), indent=2, sort_keys=True))
        return 0
    if args.verify_bundle:
        print(json.dumps(verify_snapshot_bundle(args.verify_bundle), indent=2, sort_keys=True))
        return 0
    if not args.input:
        parser.error("input is required for this report")
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
    elif args.report == "review-priority":
        snapshot = review_priority_summary(records)
    elif args.report == "review-diff":
        if not args.from_build or not args.to_build:
            parser.error("--from-build and --to-build are required for review-diff")
        snapshot = compare_review_priority(records, args.from_build, args.to_build)
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
                                      has_open_questions=True if args.open_questions else None,
                                      high_priority_only=args.high_priority_review)
    if args.create_bundle:
        create_snapshot_bundle(snapshot, args.create_bundle)
        print(json.dumps({"bundle": str(args.create_bundle), "created": True,
                          "read_only": True, "runtime_approval": False}, sort_keys=True))
        return 0
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
