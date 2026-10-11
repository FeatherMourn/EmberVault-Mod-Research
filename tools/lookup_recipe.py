"""Run a deterministic, read-only recipe lookup against an offline index."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from src.recipe_index import load_recipe_index, lookup_recipe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path, help="Offline JSON research record index")
    parser.add_argument("recipe_id")
    parser.add_argument("--build", required=True)
    args = parser.parse_args()
    result = lookup_recipe(load_recipe_index(args.index), args.recipe_id, args.build)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
