"""Fail-closed verifier for independent recipe customization evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = (
    "craftingDuration", "output_count", "input_itemStack_count",
    "typed_workshopId_replacement", "requiredProps_clear_on_clone",
    "knowledgeRequirement_clear_on_clone", "clone_registration_reached",
)


def verify(path: Path) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"schema": "control_center.recipe_customization_evidence_verification.v1", "valid": False, "errors": [str(exc)]}
    if data.get("schema") not in {
        "control_center.recipe_knowledge_requirement_runtime_evidence.v2",
        "control_center.recipe_knowledge_requirement_runtime_evidence.v3",
    }:
        errors.append("unsupported evidence schema")
    if data.get("feature_state") != "research-only":
        errors.append("recipe customization must remain research-only")
    for field in ("clone_item_id", "clone_recipe_id"):
        if not isinstance(data.get(field), int) or data[field] <= 0:
            errors.append(f"{field} must be a positive integer")
    if data.get("clone_item_id") == data.get("clone_recipe_id"):
        errors.append("clone item and recipe IDs must differ")
    evidence = data.get("evidence", {})
    required_fields = REQUIRED if data.get("schema", "").endswith(".v2") else ("clone_registration_reached",)
    for field in required_fields:
        if evidence.get(field) is not True:
            errors.append(f"evidence {field} is not verified")
    if data.get("schema", "").endswith(".v3"):
        for field in ("knowledge_requirement_replacement", "replacement_donor_found"):
            if evidence.get(field) is not True:
                errors.append(f"evidence {field} is not verified")
    if evidence.get("panic_or_loader_error") is not False:
        errors.append("panic_or_loader_error must be false")
    cleanup = data.get("cleanup", {})
    for field in ("game_stopped", "probe_uninstalled", "stable_profile_restored"):
        if cleanup.get(field) is not True:
            errors.append(f"cleanup {field} must be true")
    if not data.get("limitations"):
        errors.append("limitations must remain documented")
    return {
        "schema": "control_center.recipe_customization_evidence_verification.v1",
        "valid": not errors,
        "path": str(path.resolve()),
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
