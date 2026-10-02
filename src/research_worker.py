#!/usr/bin/env python3
"""Isolated, read-only Research worker boundary."""
from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="")
    parser.add_argument("--operation", default="")
    parser.add_argument("--game-path", default="")
    parser.add_argument("--backup", default="")
    parser.add_argument("--settings-manifest", default="")
    args = parser.parse_args()
    payload = {"contract_version": 1,
        "status": "ready" if args.profile == "research" else "blocked",
        "message": "Research worker prepared a read-only evidence session." if args.profile == "research" else "Research requires the isolated research profile.",
        "data": {"profile_id": args.profile, "operation_id": args.operation, "application_state": "read-only", "mutates_workspace": False}}
    print(json.dumps(payload))
    return 0 if payload["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
