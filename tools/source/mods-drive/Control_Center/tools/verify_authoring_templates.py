"""Validate the shipped reusable authoring-template set."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
REQUIRED = {
    "module_manifest_template.json": "control_center.module_manifest.v1",
    "clone_definition_template.json": "control_center.clone_definition.v1",
    "recipe_definition_template.json": "control_center.recipe_definition.v1",
    "localization_definition_template.json": "control_center.localization_definition.v1",
    "visual_variant_template.json": "control_center.visual_variant.v1",
    "research_probe_template.json": "control_center.research_probe.v1",
    "interaction_donor_probe_template.json": "control_center.interaction_donor_probe.v1",
    "compatibility_report_template.json": "control_center.compatibility_report.v1",
    "evidence_report_template.json": "control_center.evidence_report.v1",
    "recovery_manifest_template.json": "control_center.recovery_manifest.v1",
    "tuning_profile_template.json": "control_center.tuning_profile.v1",
    "builder_plan_template.json": "control_center.builder_plan.v1",
    "capability_record_template.json": "control_center.capability_record.v1",
    "animation_graph_variant_template.json": "control_center.animation_graph_variant.v1",
    "world_generation_plan_template.json": "control_center.world_generation_plan.v1",
}
def verify(directory: Path) -> dict:
    errors=[]; checked=0
    for filename, schema in REQUIRED.items():
        path=Path(directory)/filename
        if not path.is_file(): errors.append(f"missing template: {filename}"); continue
        try: data=json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc: errors.append(f"invalid JSON in {filename}: {exc}"); continue
        checked += 1
        if data.get("schema") != schema: errors.append(f"wrong schema in {filename}")
        if filename == "interaction_donor_probe_template.json":
            required = {
                "feature_state": "research-only",
                "runtime_mutation": False,
                "execution_scope": "single-player-read-only",
                "save_policy": "do-not-save-until-explicitly-approved",
                "authority": "unknown",
                "persistence": "unknown",
                "replication": "unknown",
            }
            for key, expected in required.items():
                if data.get(key) != expected:
                    errors.append(f"unsafe interaction template field: {key}")
            if not isinstance(data.get("prohibited_actions"), list) or not data["prohibited_actions"]:
                errors.append("interaction template must declare prohibited actions")
        if filename == "visual_variant_template.json":
            if data.get("feature_state") != "research-only":
                errors.append("visual variant must remain research-only until rendering is verified")
            if not isinstance(data.get("donor_item_id"), int) or data["donor_item_id"] <= 0:
                errors.append("visual variant donor_item_id must be a positive integer")
            for key in ("materials", "textures", "color_adjustments"):
                if not isinstance(data.get(key), list):
                    errors.append(f"visual variant {key} must be a list")
            for key in ("materials", "textures"):
                for index, entry in enumerate(data.get(key, [])):
                    if not isinstance(entry, dict):
                        errors.append(f"visual variant {key}[{index}] must be an object")
                    elif not str(entry.get("resource_guid", "")).strip():
                        errors.append(f"visual variant {key}[{index}] requires resource_guid")
            for index, entry in enumerate(data.get("color_adjustments", [])):
                if not isinstance(entry, dict):
                    errors.append(f"visual variant color_adjustments[{index}] must be an object")
                elif not re.fullmatch(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?", str(entry.get("color", ""))):
                    errors.append(f"visual variant color_adjustments[{index}] requires #RRGGBB or #RRGGBBAA color")
            color_plan = data.get("item_color_combination")
            if color_plan is not None:
                if not isinstance(color_plan, dict) or color_plan.get("runtime_field") != "itemColorCombinationSetup":
                    errors.append("visual variant item_color_combination has an invalid runtime field")
                else:
                    for channel in ("color0", "color1", "color2"):
                        value = color_plan.get(channel)
                        if not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
                            errors.append(f"visual variant item_color_combination.{channel} requires a packed 32-bit color")
                    if color_plan.get("isSet") is not True:
                        errors.append("visual variant item_color_combination.isSet must be true")
            for key in ("scale", "offset"):
                value = data.get(key)
                if not isinstance(value, list) or len(value) != 3 or not all(isinstance(item, (int, float)) for item in value):
                    errors.append(f"visual variant {key} must contain exactly three numeric values")
            for key in ("catalog_preview", "placement_preview"):
                if data.get(key) not in {"donor-fallback", "replacement-preview", "unverified"}:
                    errors.append(f"visual variant {key} has an unsafe preview policy")
        if filename == "animation_graph_variant_template.json":
            if data.get("feature_state") != "research-only":
                errors.append("animation graph variant must remain research-only")
            if data.get("graph_type") != "keen::anim_graph::runtime_graph::AnimationGraphResource2_0":
                errors.append("animation graph variant uses an unsupported graph type")
            owner = data.get("owner", {})
            if owner.get("type") != "keen::NpcCollection" or owner.get("field") != "uiRendering.animationGraph2":
                errors.append("animation graph variant owner boundary is unsafe")
            if data.get("edit", {}).get("kind") != "state_pose_redirect" or data.get("edit", {}).get("same_graph_existing_pose") is not True:
                errors.append("animation graph variant edit must be a same-graph state pose redirect")
            required = {"modify-donor", "modify-template", "create-or-mutate-entity", "write-world", "write-save", "modify-animation-payload"}
            if not required.issubset(set(data.get("prohibited_actions", []))):
                errors.append("animation graph variant is missing prohibited actions")
        if filename == "world_generation_plan_template.json":
            if data.get("feature_state") != "research-only":
                errors.append("world generation plan must remain research-only")
            required = {"read-voxel-content", "write-live-world", "register-resource", "attach-resource", "write-save", "multiplayer-use"}
            if not required.issubset(set(data.get("prohibited_actions", []))):
                errors.append("world generation plan is missing prohibited actions")
            promotion = data.get("promotion", {})
            for key in ("runtime_payload_read", "authoring_verified", "save_verified", "multiplayer_verified"):
                if promotion.get(key) is not False:
                    errors.append(f"world generation promotion flag must start false: {key}")
    return {"schema":"control_center.authoring_template_verification.v1","valid":not errors,"checked":checked,"required":len(REQUIRED),"errors":errors}
def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("directory",type=Path); args=parser.parse_args()
    result=verify(args.directory); print(json.dumps(result,indent=2)); return 0 if result["valid"] else 1
if __name__ == "__main__": raise SystemExit(main())
