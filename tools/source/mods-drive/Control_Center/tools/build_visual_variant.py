"""Build a validated research-only visual-variant definition from a template."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.asset_substitution import AssetSubstitutionPlanner


def build(template: Path, output: Path, new_item_id: int) -> dict:
    data = json.loads(Path(template).read_text(encoding="utf-8-sig"))
    if data.get("schema") != "control_center.visual_variant.v1":
        raise ValueError("template schema must be control_center.visual_variant.v1")
    for key in ("scale", "offset"):
        value = data.get(key)
        if (not isinstance(value, list) or len(value) != 3 or
                not all(isinstance(item, (int, float)) for item in value)):
            raise ValueError(f"{key} must contain exactly three numeric values")
    for key in ("catalog_preview", "placement_preview"):
        if data.get(key) not in {"donor-fallback", "replacement-preview", "unverified"}:
            raise ValueError(f"unsafe {key} policy")
    donor = data.get("donor_item_id")
    model = data.get("replacement_model_guid")
    substitutions = []
    if model:
        substitutions.append({"field": "visualModel", "resource_guid": model,
                              "ownership": "external-research"})
    for field, entries in (("material", data.get("materials", [])),
                           ("texture", data.get("textures", []))):
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"{field} entries must be objects")
            substitutions.append({"field": field, "resource_guid": entry.get("resource_guid", ""),
                                  "resource_type": entry.get("resource_type", ""),
                                  "ownership": entry.get("ownership", "external-research")})
    plan = AssetSubstitutionPlanner().plan(donor, new_item_id, substitutions,
                                           data.get("color_adjustments", []))
    result = dict(data)
    result["new_item_id"] = new_item_id
    result["feature_state"] = "research-only"
    result["mechanics_policy"] = plan.mechanics_policy
    result["validated_plan"] = AssetSubstitutionPlanner.manifest_metadata(plan)
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("new_item_id", type=int)
    args = parser.parse_args()
    build(args.template, args.output, args.new_item_id)
    print(f"Generated visual variant: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
