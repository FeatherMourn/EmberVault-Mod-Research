"""Plan or explicitly apply a reversible isolated smoke-test profile."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.recovery import ModQuarantineService, RecoveryError


def load_profile(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != "control_center.smoke_profile.v1":
        raise ValueError("unsupported smoke profile schema")
    excluded = data.get("exclude_modules", [])
    retained = data.get("retain_modules", [])
    if not isinstance(excluded, list) or not all(isinstance(item, str) for item in excluded):
        raise ValueError("exclude_modules must be a string array")
    if not isinstance(retained, list) or not all(isinstance(item, str) for item in retained):
        raise ValueError("retain_modules must be a string array")
    if set(excluded) & set(retained):
        raise ValueError("a module cannot be both retained and excluded")
    data["exclude_modules"] = excluded
    data["retain_modules"] = retained
    return data


def plan(game_dir: Path, profile_path: Path, state_dir: Path) -> dict:
    profile = load_profile(profile_path)
    mods = Path(game_dir).resolve() / "mods"
    live = sorted(item.name for item in mods.iterdir() if item.is_dir()) if mods.is_dir() else []
    excluded = set(profile["exclude_modules"])
    retained = set(profile["retain_modules"])
    result = {
        "profile": profile.get("id"),
        "game_dir": str(Path(game_dir).resolve()),
        "state_dir": str(Path(state_dir).resolve()),
        "exclude": sorted(excluded & set(live)),
        "missing_exclusions": sorted(excluded - set(live)),
        "unaccounted_live_modules": sorted(set(live) - excluded - retained),
        "research_only_exclusions": [],
        "status": "ready" if excluded <= set(live) and set(live) <= excluded | retained else "review_required",
    }
    for mod_id in sorted(excluded & set(live)):
        try:
            manifest = json.loads((mods / mod_id / "mod.json").read_text(encoding="utf-8-sig"))
            if manifest.get("feature_state") == "research-only" or manifest.get("research_only") is True:
                result["research_only_exclusions"].append(mod_id)
        except (OSError, ValueError):
            continue
    logs = Path(game_dir).resolve() / "logs"
    candidates = sorted(logs.glob("*.eml.log"), key=lambda item: item.stat().st_mtime, reverse=True) if logs.is_dir() else []
    if candidates:
        latest = candidates[0]
        result["log_baseline"] = {
            "path": str(latest),
            "mtime": latest.stat().st_mtime,
            "size": latest.stat().st_size,
        }
    else:
        result["log_baseline"] = None
    return result


def game_running() -> bool:
    result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Enshrouded.exe"], capture_output=True, text=True, check=False)
    return "Enshrouded.exe" in result.stdout


def restore_profile(state_dir: Path, profile_id: str) -> list[str]:
    """Restore every module owned by one isolated smoke profile.

    Restoration must not depend on the excluded modules still being present in
    the live directory: their absence is the expected state after quarantine.
    """
    service = ModQuarantineService(state_dir)
    profile_label = f"isolated smoke profile {profile_id}"
    records = [record for record in service.records() if record.reason == profile_label]
    return [str(service.restore(record.record_path)) for record in records]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game_dir", type=Path)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--state-dir", type=Path, default=Path(__file__).resolve().parents[1] / "profiles")
    parser.add_argument("--apply", action="store_true", help="quarantine excluded modules; omitted means dry run")
    parser.add_argument("--restore", action="store_true", help="restore modules quarantined for this profile")
    args = parser.parse_args()
    try:
        if args.apply and args.restore:
            raise ValueError("--apply and --restore cannot be used together")
        result = plan(args.game_dir, args.profile, args.state_dir)
        if result["status"] != "ready" and not args.restore:
            print(json.dumps(result, indent=2)); return 2
        if args.restore:
            if game_running():
                raise RecoveryError("Enshrouded is running; close it before restoring a smoke profile.")
            result["restored"] = restore_profile(args.state_dir, result["profile"])
            result["status"] = "restored"
        elif args.apply:
            if game_running():
                raise RecoveryError("Enshrouded is running; close it before applying a smoke profile.")
            service = ModQuarantineService(args.state_dir)
            records = [service.quarantine(Path(args.game_dir) / "mods", mod_id, f"isolated smoke profile {result['profile']}") for mod_id in result["exclude"]]
            result["applied"] = [{"mod_id": record.mod_id, "record": str(record.record_path)} for record in records]
            result["status"] = "applied"
        else:
            result["status"] = "dry_run"
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, RecoveryError) as exc:
        print(f"profile application failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
