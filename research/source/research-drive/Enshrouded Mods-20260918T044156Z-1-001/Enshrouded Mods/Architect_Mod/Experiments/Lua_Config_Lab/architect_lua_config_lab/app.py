"""Architect Lua Config Lab - entry point.

CLI usage
---------
    python app.py                      launch the GUI
    python app.py parse                load schema and print regression counts
    python app.py search <query>       search resource roots
    python app.py generate <profile>   print generated Lua for a profile
    python app.py export <profile>     export a profile as an EML mod
"""

from __future__ import annotations

import argparse
import os
import sys

from . import __identifier__, __tool_name__, __version__
from .config import (
    base_lua_path,
    cache_dir,
    kfc_dir,
    output_dir,
    types_lua_path,
)


def _build_lab(args):
    from .core.lab import Lab

    lab = Lab(
        types_lua_path=args.types_lua or types_lua_path(),
        base_lua_path=args.base_lua or base_lua_path(),
        kfc_dir=args.kfc_dir or kfc_dir(),
        cache_dir=None if args.no_cache else cache_dir(),
    )
    lab.load(force_rebuild=args.rebuild)
    return lab


def cmd_parse(args) -> int:
    lab = _build_lab(args)
    db = lab.schema()
    print("types.lua:", lab.types_lua_path)
    print("  classes:", db.class_count())
    print("  aliases:", db.alias_count())
    print("  fields: ", db.field_count())
    print("  resource roots:", len(lab.root_entries()))
    from .core.kfc_roots import direct_field_count, reachable_nested_class_names
    print("  direct fields on roots:", direct_field_count(db, lab.root_entries()))
    print("  reachable nested classes:",
          len(reachable_nested_class_names(db, lab.root_entries())))
    print("  types.lua sha256:", lab.types_sha256)
    return 0


def cmd_search(args) -> int:
    lab = _build_lab(args)
    query = " ".join(args.query)
    for entry in lab.search(query):
        print("%-45s %-55s %s" % (
            entry["family"], entry["lua_class"], entry["resource_type"]))
    return 0


def cmd_generate(args) -> int:
    from .core.profile import load_profile

    lab = _build_lab(args)
    profile = load_profile(args.profile)
    problem = profile.validate()
    if problem:
        print("profile invalid:", problem, file=sys.stderr)
        return 2
    print(lab.generate(profile))
    return 0


def cmd_export(args) -> int:
    from .core.profile import load_profile

    lab = _build_lab(args)
    profile = load_profile(args.profile)
    problem = profile.validate()
    if problem:
        print("profile invalid:", problem, file=sys.stderr)
        return 2
    mismatch, revalidations = lab.compatibility(profile)
    if mismatch:
        print("WARNING: schema version mismatch (profile types_lua_sha256 differs).")
        for item in revalidations:
            print("  ", item)
    paths = lab.export(
        profile,
        base_output_dir=args.output or output_dir(),
        overwrite=args.overwrite,
    )
    print("Exported mod to:", paths["directory"])
    for key in ("mod_json", "mod_lua", "profile_json", "manifest"):
        print("  %s: %s" % (key, paths[key]))
    return 0


def cmd_gui(args) -> int:
    from .ui.main_window import launch

    return launch(args)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog=__identifier__,
        description="%s v%s - startup resource configuration editor." % (
            __tool_name__, __version__),
    )
    parser.add_argument("--types-lua", help="path to types.lua")
    parser.add_argument("--base-lua", help="path to base.lua")
    parser.add_argument("--kfc-dir", help="path to the KFC resource files directory")
    parser.add_argument("--no-cache", action="store_true", help="disable schema cache")
    parser.add_argument("--rebuild", action="store_true", help="force schema cache rebuild")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("parse", help="load schema and print regression counts")

    search_p = sub.add_parser("search", help="search resource roots")
    search_p.add_argument("query", nargs="*")

    gen_p = sub.add_parser("generate", help="print generated Lua for a profile")
    gen_p.add_argument("profile")

    exp_p = sub.add_parser("export", help="export a profile as an EML mod")
    exp_p.add_argument("profile")
    exp_p.add_argument("--output")
    exp_p.add_argument("--overwrite", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "parse":
        return cmd_parse(args)
    if args.command == "search":
        return cmd_search(args)
    if args.command == "generate":
        return cmd_generate(args)
    if args.command == "export":
        return cmd_export(args)
    return cmd_gui(args)


if __name__ == "__main__":
    raise SystemExit(main())
