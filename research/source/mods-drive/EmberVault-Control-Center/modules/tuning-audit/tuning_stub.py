"""Read-only audit for staged gameplay settings.

This worker verifies only the execution context. It intentionally does not
apply, inject, or rewrite any game configuration.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="")
    parser.add_argument("--game-path", default="")
    parser.add_argument("--operation", default="")
    parser.add_argument("--settings-manifest", default="")
    args = parser.parse_args()
    game = Path(args.game_path) if args.game_path else None
    manifest = Path(args.settings_manifest) if args.settings_manifest else None
    manifest_valid = False
    if manifest and manifest.is_file():
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_valid = payload.get("application_state") == "staged-only" and payload.get("schema_version") == 1
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            manifest_valid = False
    checks = [
        f"profile_selected: {bool(args.profile)}",
        f"game_path_configured: {bool(args.game_path)}",
        f"game_path_exists: {game.exists() if game else False}",
        f"settings_manifest_configured: {bool(args.settings_manifest)}",
        f"settings_manifest_valid: {manifest_valid}",
        "settings_source: staged-profile-values",
        "live_game_settings_changed: False",
    ]
    print(json.dumps({
        "contract_version": 1,
        "status": "ready",
        "read_only": True,
        "profile": args.profile,
        "game_path": args.game_path,
        "operation": args.operation,
        "checks": checks,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
