"""Non-mutating Content Creator design-workspace audit."""
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
              "design_workspace_only: True",
              "live_game_content_touched: False",
              f"recovery_context_available: {bool(args.backup)}"]
    print(json.dumps({"contract_version": 1, "status": "ready", "read_only": True,
                      "profile": args.profile, "game_path": args.game_path, "operation": args.operation,
                      "checks": checks}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
