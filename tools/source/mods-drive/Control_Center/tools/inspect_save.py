"""Inspect the supported Enshrouded character-save surface without writing."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.enshrouded_save_reader import SaveFormatError, discover_save_directories, inspect_save_directory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("save_folder", type=Path, nargs="?")
    parser.add_argument("--discover", action="store_true", help="list standard save locations without reading or changing them")
    args = parser.parse_args()
    if args.discover:
        print(json.dumps(discover_save_directories(), indent=2, sort_keys=True))
        return 0
    if args.save_folder is None:
        parser.error("save_folder is required unless --discover is used")
    try:
        print(json.dumps(inspect_save_directory(args.save_folder), indent=2, sort_keys=True))
        return 0
    except (OSError, SaveFormatError) as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
