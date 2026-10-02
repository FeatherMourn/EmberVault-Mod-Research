"""Generate a research-only furniture clone probe from the proven runtime template."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("donor_item_id", type=int)
    parser.add_argument("donor_recipe_id", type=int)
    parser.add_argument("new_item_id", type=int)
    parser.add_argument("new_recipe_id", type=int)
    parser.add_argument("debug_name")
    parser.add_argument(
        "--log-prefix",
        default="[CC-BED-CLONE] ",
        help="Log marker used by evidence tools; kept bed-compatible by default.",
    )
    args = parser.parse_args()
    if min(args.donor_item_id, args.donor_recipe_id, args.new_item_id, args.new_recipe_id) <= 0:
        parser.error("all IDs must be positive")
    if not args.debug_name.strip():
        parser.error("debug_name is required")
    if not args.log_prefix.strip() or not args.log_prefix.endswith(" "):
        parser.error("log-prefix must be non-empty and end with a space")
    source_path = args.template / "src" / "mod.lua" if args.template.is_dir() else args.template
    source = source_path.read_text(encoding="utf-8")
    # Templates may represent different furniture donors, so do not assume
    # the original bed constants or debug names.  Restrict each replacement
    # to its declaration/recipe comparison to avoid altering unrelated data.
    replacements = (
        (r"local DONOR_ID = \d+", f"local DONOR_ID = {args.donor_item_id}"),
        (r"local NEW_ITEM_ID = \d+", f"local NEW_ITEM_ID = {args.new_item_id}"),
        (r"local NEW_RECIPE_ID = \d+", f"local NEW_RECIPE_ID = {args.new_recipe_id}"),
        (r"value == \d+", f"value == {args.donor_recipe_id}"),
        (r"local PREFIX = .+", "local PREFIX = " + json.dumps(args.log_prefix)),
    )
    for pattern, replacement in replacements:
        source, count = re.subn(pattern, replacement, source, count=1)
        if count != 1:
            raise SystemExit(f"template marker not found: {pattern}")
    # The generated template uses the donor's original clone name in both the
    # item and recipe records. Replace the first matching custom-name literals
    # without depending on the donor type.
    source, count = re.subn(r"(clone\.data\.debugName\s*=\s*)['\"][^'\"]+['\"]", r"\g<1>" + json.dumps(args.debug_name.strip()), source, count=1)
    if count != 1:
        raise SystemExit("template clone debug name not found")
    source, count = re.subn(r"(new_recipe\.debugName\s*=\s*)['\"][^'\"]+['\"]", r"\g<1>" + json.dumps(args.debug_name.strip() + "_Recipe"), source, count=1)
    if count != 1:
        raise SystemExit("template clone recipe debug name not found")
    if args.output.exists():
        raise SystemExit(f"output already exists: {args.output}")
    (args.output / "src").mkdir(parents=True)
    (args.output / "src" / "mod.lua").write_text(source, encoding="utf-8")
    manifest = {
        "schema": "control_center.furniture_clone_probe.v1",
        "id": args.output.name,
        "name": "Control Center Furniture Clone Probe",
        "version": "0.1.0",
        "author": "Enshrouded Control Center",
        "capabilities": ["patch"],
        "feature_state": "research-only",
        "entrypoint": "src/mod.lua",
        "donor_item_id": args.donor_item_id,
        "donor_recipe_id": args.donor_recipe_id,
        "new_item_id": args.new_item_id,
        "new_recipe_id": args.new_recipe_id,
        "debug_name": args.debug_name.strip(),
        "runtime_mutation": True,
        "rollback": "remove this module while the game is stopped and restore the stable profile",
    }
    (args.output / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated furniture clone probe: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
