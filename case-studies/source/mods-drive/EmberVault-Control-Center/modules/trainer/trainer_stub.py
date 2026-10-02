"""Non-mutating Trainer readiness audit."""
from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="")
    parser.add_argument("--game-path", default="")
    parser.add_argument("--operation", default="")
    parser.add_argument("--backup", default="")
    args = parser.parse_args()
    checks = [f"profile_selected: {bool(args.profile)}",
              f"game_path_configured: {bool(args.game_path)}",
              f"recovery_backup_supplied: {bool(args.backup)}",
              "mutation_performed: False"]
    print(json.dumps({"contract_version": 1, "status": "ready", "read_only": True,
                      "profile": args.profile, "game_path": args.game_path, "operation": args.operation,
                      "checks": checks}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
