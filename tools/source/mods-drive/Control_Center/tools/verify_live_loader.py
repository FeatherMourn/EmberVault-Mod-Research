"""Preflight a live EML installation before running a content probe."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def _build_id(value: object) -> str | None:
    """Return the stable numeric build prefix from an EML version string."""
    if value is None:
        return None
    text = str(value).strip()
    return text.split("|", 1)[0].strip() or None


def inspect(game_dir: Path, mod_id: str | None = None, log_since: float | None = None,
            expected_build: str | None = None) -> dict:
    game_dir = Path(game_dir).resolve()
    mods = game_dir / "mods"
    log_dir = game_dir / "logs"
    result = {
        "game_dir": str(game_dir),
        "dinput8": {"exists": (game_dir / "dinput8.dll").is_file()},
        "mods_dir": {"exists": mods.is_dir()},
        "logs_dir": {"exists": log_dir.is_dir()},
        "mods": [],
        "research_only_mods": [],
        "unclassified_mods": [],
        "unclassified_reasons": {},
        "external_third_party_mods": [],
        "external_third_party_reasons": {},
        "classification_counts": {"stable": 0, "experimental": 0, "research-only": 0, "disabled": 0, "unclassified": 0},
        "latest_eml_log": None,
        "game_build": None,
        "warnings": [],
        "status": "ready",
    }
    if not result["dinput8"]["exists"] or not result["mods_dir"]["exists"]:
        result["status"] = "not_ready"
        return result
    known_external = {}
    known_path = Path(__file__).resolve().parents[1] / "research" / "KNOWN_EXTERNAL_MODULES_20260929.json"
    try:
        known_external = json.loads(known_path.read_text(encoding="utf-8")).get("modules", {})
    except (OSError, ValueError, TypeError):
        known_external = {}
    for folder in sorted(path for path in mods.iterdir() if path.is_dir()):
        manifest = folder / "mod.json"
        entry = {"id": folder.name, "path": str(folder), "manifest": manifest.is_file()}
        if not manifest.is_file():
            result["unclassified_mods"].append(folder.name)
            result["unclassified_reasons"][folder.name] = "missing mod.json"
            result["classification_counts"]["unclassified"] += 1
        else:
            try:
                data = json.loads(manifest.read_text(encoding="utf-8-sig"))
                entry.update({"manifest_id": data.get("id"), "entrypoint": data.get("entrypoint"),
                              "capabilities": data.get("capabilities", []),
                              "feature_state": data.get("feature_state")})
                if data.get("feature_state") == "research-only" or data.get("research_only") is True:
                    result["research_only_mods"].append(folder.name)
                    result["classification_counts"]["research-only"] += 1
                elif not data.get("feature_state"):
                    external = known_external.get(folder.name)
                    if external:
                        result["external_third_party_mods"].append(folder.name)
                        result["external_third_party_reasons"][folder.name] = external.get("reason", "known third-party module")
                    else:
                        result["unclassified_mods"].append(folder.name)
                        result["unclassified_reasons"][folder.name] = "missing feature_state"
                        result["classification_counts"]["unclassified"] += 1
                elif data.get("feature_state") in result["classification_counts"]:
                    result["classification_counts"][data["feature_state"]] += 1
                else:
                    result["unclassified_mods"].append(folder.name)
                    result["unclassified_reasons"][folder.name] = "unsupported feature_state"
                    result["classification_counts"]["unclassified"] += 1
            except (OSError, ValueError) as exc:
                entry["manifest_error"] = str(exc)
                result["unclassified_mods"].append(folder.name)
                result["unclassified_reasons"][folder.name] = "invalid mod.json"
                result["classification_counts"]["unclassified"] += 1
        result["mods"].append(entry)
    if result["research_only_mods"]:
        result["warnings"].append("research-only modules are installed; use an isolated profile for production smoke tests")
    if result["unclassified_mods"]:
        result["warnings"].append("modules without an explicit feature_state require manual compatibility review")
    if result["external_third_party_mods"]:
        result["warnings"].append("known third-party modules are present; isolation remains disabled until they are deliberately reviewed")
    result["isolation_ready"] = not result["research_only_mods"] and not result["unclassified_mods"] and not result["external_third_party_mods"]
    if mod_id:
        selected = next((item for item in result["mods"] if item["id"] == mod_id), None)
        result["selected_mod"] = selected
        if not selected or not selected.get("manifest"):
            result["status"] = "mod_not_ready"
        elif selected.get("entrypoint") and not (Path(selected["path"]) / selected["entrypoint"]).is_file():
            result["status"] = "entrypoint_missing"
        elif "patch" not in selected.get("capabilities", []):
            result["status"] = "patch_capability_missing"
    if log_dir.is_dir():
        logs = sorted(log_dir.glob("*.eml.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if logs:
            latest = logs[0]
            result["latest_eml_log"] = {"path": str(latest), "size": latest.stat().st_size,
                                         "modified": datetime.fromtimestamp(latest.stat().st_mtime, timezone.utc).isoformat()}
            if log_since is not None:
                result["log_observability"] = {
                    "baseline_mtime": log_since,
                    "latest_mtime": latest.stat().st_mtime,
                    # Avoid treating filesystem timestamp conversion noise as
                    # a new session; a real launch must advance the log by a
                    # meaningful interval.
                    "fresh_session_observed": latest.stat().st_mtime > log_since + 1.0,
                }
                if not result["log_observability"]["fresh_session_observed"]:
                    result["warnings"].append("no EML log was created or updated after the smoke-test baseline")
            try:
                text = latest.read_text(encoding="utf-8", errors="replace")
                match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
                if match:
                    result["game_build"] = match.group(1)
            except OSError:
                result["warnings"].append("latest EML log could not be read for build compatibility")
            if latest.stat().st_size >= 512 * 1024 * 1024:
                result["warnings"].append("latest EML log exceeds 512 MiB; rotate or reduce probe verbosity before another smoke test")
    if expected_build:
        expected = str(expected_build).strip()
        result["build_compatibility"] = {
            "expected": expected,
            "observed": result["game_build"],
            "status": "compatible" if _build_id(result["game_build"]) == _build_id(expected) else "review_required",
        }
        if result["build_compatibility"]["status"] != "compatible":
            result["warnings"].append("observed EML build does not match the expected build")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game_dir", type=Path)
    parser.add_argument("--mod-id")
    parser.add_argument("--profile", type=Path, help="validate a smoke-profile JSON against the live module inventory")
    parser.add_argument("--require-isolated", action="store_true",
                        help="fail when research-only or unclassified modules are installed")
    parser.add_argument("--allow-research-only", action="store_true",
                        help="with --require-isolated, allow explicitly isolated research modules")
    parser.add_argument("--log-since", type=float,
                        help="baseline log mtime; report whether a fresh EML session was observed")
    parser.add_argument("--expected-build",
                        help="fail compatibility reporting unless the latest EML log reports this exact build")
    parser.add_argument("--output", type=Path, help="also save the preflight snapshot as JSON")
    args = parser.parse_args()
    result = inspect(args.game_dir, args.mod_id, args.log_since, args.expected_build)
    if args.profile:
        try:
            profile = json.loads(args.profile.read_text(encoding="utf-8"))
            excluded = set(profile.get("exclude_modules", []))
            retained = set(profile.get("retain_modules", []))
            live = {item["id"] for item in result["mods"]}
            result["profile_check"] = {
                "id": profile.get("id"),
                "missing_exclusions": sorted(excluded - live),
                "unlisted_live_modules": sorted(live - excluded - retained),
                "status": "valid" if excluded <= live and live <= excluded | retained else "review_required",
            }
        except (OSError, ValueError, TypeError) as exc:
            result["profile_check"] = {"status": "invalid", "error": str(exc)}
            result["status"] = "profile_invalid"
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if args.require_isolated and (result["unclassified_mods"] or (result["research_only_mods"] and not args.allow_research_only)):
        return 2
    if args.profile and result.get("profile_check", {}).get("status") != "valid":
        return 2
    if args.log_since is not None and not result.get("log_observability", {}).get("fresh_session_observed", False):
        return 2
    if args.expected_build and result.get("build_compatibility", {}).get("status") != "compatible":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
