"""Create, restore, and compare verified Enshrouded save snapshots."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.save_backup import backup_save_directory, compare_save_snapshots, game_is_running, restore_save_backup
from core.enshrouded_save_reader import discover_save_directories


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    backup = sub.add_parser("backup", help="copy a save directory into a verified snapshot")
    backup.add_argument("source", type=Path); backup.add_argument("backup_root", type=Path); backup.add_argument("--label", default="manual")
    restore = sub.add_parser("restore", help="restore a verified snapshot into a destination")
    restore.add_argument("snapshot", type=Path); restore.add_argument("destination", type=Path)
    diff = sub.add_parser("diff", help="compare two verified snapshots by hash")
    diff.add_argument("before", type=Path); diff.add_argument("after", type=Path)
    sub.add_parser("discover", help="find standard save locations without reading or changing saves")
    args = parser.parse_args()
    if args.command == "discover":
        print(json.dumps(discover_save_directories(), indent=2, sort_keys=True))
        return 0
    if game_is_running():
        parser.error("Enshrouded is running; close the game before backup, restore, or diff operations")
    if args.command == "backup":
        result = backup_save_directory(args.source, args.backup_root, args.label)
    elif args.command == "restore":
        result = restore_save_backup(args.snapshot, args.destination)
    else:
        result = compare_save_snapshots(args.before, args.after)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
