"""Run the persisted Control Center save-backup policy once."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.enshrouded_save_reader import discover_save_directories
from core.save_backup import run_scheduled_backup


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one safe scheduled Enshrouded save backup")
    parser.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    base = args.base_dir.resolve()
    policy = base / "profiles" / "save-backup-policy.json"
    discovery = discover_save_directories()
    source = next((Path(item["path"]) for item in discovery["candidates"] if item["exists"] and item["has_character_index"]), None)
    if source is None:
        print(json.dumps({"status": "save_folder_not_found"}))
        return 2
    result = run_scheduled_backup(source, base / "profiles" / "save-backups", policy)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in {"created", "disabled", "not_due"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
