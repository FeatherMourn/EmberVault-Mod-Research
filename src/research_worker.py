#!/usr/bin/env python3
"""Isolated, read-only Research worker boundary."""
from __future__ import annotations

import argparse
import json

from embervault_sdk import ModuleResult


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="")
    parser.add_argument("--operation", default="")
    parser.add_argument("--game-path", default="")
    parser.add_argument("--backup", default="")
    parser.add_argument("--settings-manifest", default="")
    args = parser.parse_args()
    ready = args.profile == "research"
    result = ModuleResult(
        "ready" if ready else "blocked",
        "Research worker prepared a read-only evidence session." if ready else "Research requires the isolated research profile.",
        {"profile_id": args.profile, "operation_id": args.operation, "application_state": "read-only", "mutates_workspace": False,
         "evidence": [],
         "recovery": {"expectation": "Read-only research worker", "rollback": "Terminate the worker", "verification": "Confirm no game or save files changed", "backup_required": False}},
    )
    print(json.dumps(result.to_dict()))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
