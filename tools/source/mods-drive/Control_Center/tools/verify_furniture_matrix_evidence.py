"""Fail-closed verifier for a multi-donor furniture runtime evidence record."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(path: Path) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"schema": "control_center.furniture_matrix_evidence_verification.v1", "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.furniture_donor_matrix_runtime_evidence.v1":
        errors.append("unsupported evidence schema")
    fresh = data.get("fresh_session", {})
    if not fresh.get("fresh_boundary_observed"):
        errors.append("fresh EML boundary was not observed")
    if int(fresh.get("final_size", 0)) <= int(fresh.get("baseline_size", 0)):
        errors.append("final log is not larger than the baseline")
    runs = data.get("runs", [])
    if len(runs) < 3:
        errors.append("at least three donor runs are required")
    item_ids = [run.get("clone_item_id") for run in runs]
    recipe_ids = [run.get("clone_recipe_id") for run in runs]
    donor_item_ids = [run.get("donor_item_id") for run in runs]
    donor_recipe_ids = [run.get("donor_recipe_id") for run in runs]
    if len(donor_item_ids) != len(set(donor_item_ids)):
        errors.append("donor item IDs are duplicated")
    if len(donor_recipe_ids) != len(set(donor_recipe_ids)):
        errors.append("donor recipe IDs are duplicated")
    if len(item_ids) != len(set(item_ids)):
        errors.append("clone item IDs are duplicated")
    if len(recipe_ids) != len(set(recipe_ids)):
        errors.append("clone recipe IDs are duplicated")
    for index, run in enumerate(runs):
        prefix = f"runs[{index}]"
        if run.get("registration") != "verified":
            errors.append(f"{prefix} registration is not verified")
        if not run.get("clone_discovered"):
            errors.append(f"{prefix} clone discovery is not verified")
        for field in ("donor_item_id", "donor_recipe_id", "clone_item_id", "clone_recipe_id"):
            if not isinstance(run.get(field), int) or run[field] <= 0:
                errors.append(f"{prefix}.{field} must be a positive integer")
        for field in ("item_registry_increment", "recipe_registry_increment", "knowledge_link_increment", "ui_set_clone_increment"):
            if run.get(field) != 1:
                errors.append(f"{prefix}.{field} must equal one")
    results = data.get("session_results", {})
    for field in ("vanilla_overwrite_detected", "duplicate_registration_detected", "panic_or_loader_error_detected"):
        if results.get(field) is not False:
            errors.append(f"session result {field} must be false")
    cleanup = data.get("cleanup", {})
    for field in ("research_probe_directories_removed", "stable_profile_restored", "live_isolation_ready"):
        if cleanup.get(field) is not True:
            errors.append(f"cleanup result {field} must be true")
    return {
        "schema": "control_center.furniture_matrix_evidence_verification.v1",
        "valid": not errors,
        "path": str(path.resolve()),
        "run_count": len(runs),
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
