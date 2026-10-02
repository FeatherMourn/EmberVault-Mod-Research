"""Render a safe, non-mutating update-recovery plan from module manifests."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.update_recovery import plan_metadata, plan_update_recovery


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("previous_build")
    parser.add_argument("current_build")
    parser.add_argument("manifests", type=Path, nargs="+",
                        help="module manifest JSON files")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    modules = []
    for path in args.manifests:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise SystemExit(f"manifest is not an object: {path}")
        modules.append(data)
    result = plan_metadata(plan_update_recovery(args.previous_build, args.current_build, modules))
    rendered = json.dumps(result, indent=2) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
