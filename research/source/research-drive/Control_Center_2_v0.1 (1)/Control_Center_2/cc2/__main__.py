"""CLI and GUI launcher. Run python -m cc2 --help."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .catalog import CatalogError, index_archives, search_items, get_item, diagnostics
from .planner import plan_new_item, save_plan
from .graph import build_graph, markdown_report

APP_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = APP_ROOT / "workspace" / "catalog.sqlite3"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="control-center-2", description="Isolated read-only KFC research + custom-content plan generator")
    p.add_argument("--db", type=Path, default=DEFAULT_DB, help="derived SQLite catalog (default: workspace/catalog.sqlite3)")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("gui", help="launch desktop window")
    cmd = sub.add_parser("index", help="index a local KFC ZIP directory (no modifications)")
    cmd.add_argument("--kfc", type=Path, required=True)
    cmd = sub.add_parser("search", help="search verified vanilla items by debug name, category, numeric ID")
    cmd.add_argument("text")
    cmd.add_argument("--limit", type=int, default=30)
    cmd = sub.add_parser("inspect", help="inspect resource dependencies of a vanilla item")
    cmd.add_argument("identity", help="item GUID or observed numeric ID")
    sub.add_parser("diagnose", help="static reference-health report")
    cmd = sub.add_parser("plan", help="create an experimental, non-deployable clone plan")
    cmd.add_argument("identity", help="registered vanilla item GUID or numeric ID")
    cmd.add_argument("--slug", required=True)
    cmd.add_argument("--name", required=True)
    cmd.add_argument("--recipe-guid")
    cmd.add_argument("--notes", default="")
    cmd.add_argument("--out", type=Path, required=True)
    cmd = sub.add_parser("graph", help="write an evidence-backed one-item graph and Markdown report")
    cmd.add_argument("identity")
    cmd.add_argument("--json-out", type=Path, required=True)
    cmd.add_argument("--md-out", type=Path, required=True)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd in (None, "gui"):
            from .ui import launch
            launch(args.db)
            return 0
        if args.cmd == "index":
            kfc = args.kfc.resolve()
            db = args.db.resolve()
            if db == kfc or kfc in db.parents:
                raise CatalogError("database must be outside the read-only KFC folder")
            result = index_archives(kfc, db, on_progress=lambda s: print(s, file=sys.stderr))
        elif args.cmd == "search":
            result = search_items(args.db, args.text, args.limit)
        elif args.cmd == "inspect":
            result = get_item(args.db, args.identity)
        elif args.cmd == "diagnose":
            result = diagnostics(args.db)
        elif args.cmd == "plan":
            plan = plan_new_item(args.db, args.identity, slug=args.slug, name=args.name,
                                 recipe_guid=args.recipe_guid, notes=args.notes)
            path = save_plan(plan, args.out)
            result = {"saved": str(path), "status": plan["status"],
                      "source_item": plan["source_item"], "blockers": plan["blockers"]}
        elif args.cmd == "graph":
            graph = build_graph(args.db, args.identity)
            for path, content in ((args.json_out, json.dumps(graph, indent=2, ensure_ascii=False)), (args.md_out, markdown_report(graph))):
                if path.exists(): raise CatalogError("refusing to overwrite report: " + str(path))
                path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content, encoding="utf-8")
            result = {"json": str(args.json_out), "markdown": str(args.md_out), "validation": graph["validation"]}
        else:
            raise CatalogError("unknown command")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return 0
    except (CatalogError, OSError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
