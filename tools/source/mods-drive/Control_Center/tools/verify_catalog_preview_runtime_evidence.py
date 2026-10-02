"""Validate partial or complete runtime evidence for a catalog-preview probe."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "control_center.catalog_preview_runtime_evidence.v1"


def validate(path: Path, root: Path | None = None) -> list[str]:
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    path = path.resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read evidence: {exc}"]
    errors: list[str] = []
    if data.get("schema") != SCHEMA:
        errors.append("unsupported evidence schema")
    if data.get("feature_state") != "research-only":
        errors.append("catalog-preview evidence must remain research-only")
    eml = data.get("eml", {})
    for key in ("api_version", "probe_loaded", "probe_completed_without_panic", "ui_links"):
        if key not in eml:
            errors.append(f"missing EML field: {key}")
    if eml.get("api_version") != "1.3":
        errors.append("unexpected EML API version")
    if eml.get("probe_completed_without_panic") is not True:
        errors.append("probe did not complete without panic")
    game = data.get("game", {})
    if game.get("launched") is not True:
        errors.append("game launch evidence is required")
    for key in ("main_menu_screenshot", "play_selection_screenshot", "world_entry_screenshot"):
        value = game.get(key)
        if not isinstance(value, str) or not (path.parent / value).is_file():
            errors.append(f"missing runtime screenshot: {key}")
    if data.get("verdict") not in {"partial_runtime_success", "catalog_tile_verified", "complete"}:
        errors.append("invalid runtime verdict")
    cleanup = data.get("cleanup", {})
    for key in ("game_stopped", "probe_uninstalled", "stable_profile_restored"):
        if cleanup.get(key) is not True:
            errors.append(f"cleanup not verified: {key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    errors = validate(args.evidence)
    print(json.dumps({"schema": "control_center.catalog_preview_runtime_evidence_verification.v1", "valid": not errors, "path": str(args.evidence), "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
