"""Fail-closed verifier for one furniture clone runtime-registration report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "control_center.furniture_clone_runtime_evidence.v1"


def verify(path: Path) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"schema": "control_center.furniture_clone_runtime_evidence_verification.v1", "valid": False, "errors": [str(exc)]}
    if data.get("schema") != SCHEMA:
        errors.append("unsupported evidence schema")
    if not data.get("probe") or not data.get("game_build") or not data.get("log"):
        errors.append("probe, game_build, and log are required")
    donor = data.get("donor", {})
    clone = data.get("clone", {})
    for label, record in (("donor", donor), ("clone", clone)):
        for field in ("item_id", "recipe_id"):
            if not isinstance(record.get(field), int) or record[field] <= 0:
                errors.append(f"{label}.{field} must be a positive integer")
    runtime = data.get("runtime", {})
    for field in ("clone_registered", "clone_discovered", "panic_or_loader_error"):
        if not isinstance(runtime.get(field), bool):
            errors.append(f"runtime.{field} must be boolean")
    if runtime.get("clone_registered") is not True or runtime.get("clone_discovered") is not True:
        errors.append("runtime registration and discovery must both be true")
    if runtime.get("panic_or_loader_error") is not False:
        errors.append("panic_or_loader_error must be false")
    for field in ("item_registry_increment", "recipe_registry_increment", "knowledge_link_increment", "ui_set_clone_increment"):
        if runtime.get(field) != 1:
            errors.append(f"runtime.{field} must equal one")
    cleanup = data.get("cleanup", {})
    for field in ("probe_removed", "third_party_mod_restored", "stable_profile_restored"):
        if cleanup.get(field) is not True:
            errors.append(f"cleanup.{field} must be true")
    if data.get("verdict") not in {"partial_runtime_registration", "runtime_registration"}:
        errors.append("unsupported verdict")
    return {
        "schema": "control_center.furniture_clone_runtime_evidence_verification.v1",
        "valid": not errors,
        "path": str(Path(path).resolve()),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    result = verify(parser.parse_args().evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
