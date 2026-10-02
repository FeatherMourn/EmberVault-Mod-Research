"""Verify that shipped research-probe generators fail closed by classification."""
from __future__ import annotations

import json
from pathlib import Path


GENERATORS = (
    "build_behavior_probe.py",
    "build_item_visual_reference_probe.py",
    "build_kfc_research_probe.py",
    "build_kfc_write_probe.py",
    "build_visual_candidate_probe.py",
    "build_recipe_customization_probe.py",
    "build_interaction_donor_probe.py",
    "build_animation_graph_variant_probe.py",
    "build_voxel_material_metadata_probe.py",
    "build_catalog_preview_probe.py",
)


def audit(root: Path) -> dict:
    tools = Path(root).resolve() / "tools"
    errors: list[str] = []
    results = []
    for name in GENERATORS:
        path = tools / name
        if not path.is_file():
            errors.append(f"missing generator: {name}")
            continue
        source = path.read_text(encoding="utf-8")
        labeled = '"feature_state": "research-only"' in source
        results.append({"generator": name, "research_only_label": labeled})
        if not labeled:
            errors.append(f"generator lacks research-only feature_state: {name}")
    return {"schema": "control_center.probe_generator_audit.v1", "valid": not errors, "generators": results, "errors": errors}


if __name__ == "__main__":
    result = audit(Path(__file__).resolve().parents[1])
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["valid"] else 1)
