"""Verify a recorded save-backup and read-only restore evidence record."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(path: Path) -> dict[str, object]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "control_center.save_backup_evidence.v1", "passed": False,
                "errors": [f"unable to read evidence: {exc}"]}
    if data.get("schema") != "control_center.save_backup_evidence.v1":
        errors.append("schema is not control_center.save_backup_evidence.v1")
    if data.get("game_stopped") is not True:
        errors.append("evidence must prove the game was stopped")
    backup = data.get("backup")
    restore = data.get("restore")
    if not isinstance(backup, dict) or backup.get("verified") is not True:
        errors.append("backup verification is missing or failed")
    if not isinstance(restore, dict) or restore.get("verified") is not True:
        errors.append("restore verification is missing or failed")
    if isinstance(backup, dict) and isinstance(restore, dict):
        if not isinstance(backup.get("file_count"), int) or backup["file_count"] <= 0:
            errors.append("backup file_count must be positive")
        if backup.get("file_count") != restore.get("file_count"):
            errors.append("backup and restore file counts differ")
        if backup.get("manifest_hash_verified") is not True:
            errors.append("backup manifest hash verification is missing")
        if restore.get("destination_is_temporary") is not True:
            errors.append("restore must be explicitly read-only into a temporary destination")
    cleanup = data.get("cleanup")
    if not isinstance(cleanup, dict) or cleanup.get("temporary_restore_removed") is not True:
        errors.append("temporary restore cleanup is missing")
    return {"schema": "control_center.save_backup_evidence.v1", "passed": not errors,
            "errors": errors, "source": data.get("source"),
            "backup": backup, "restore": restore, "cleanup": cleanup}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    result = verify(args.evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
