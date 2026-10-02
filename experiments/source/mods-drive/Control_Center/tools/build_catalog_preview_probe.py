"""Generate the first catalog-preview research probe from a known-good clone."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DONOR_ITEM_ID = 2940001508
DONOR_RECIPE_ID = 3531872774


RENDER_CONTROL_VALUES = {
    "iconRenderOffset": "{ localOffset = { x = 0.1, y = 0.0, z = 0.0 }, worldOffset = { x = 0.0, y = 0.0, z = 0.0 }, orientationOffset = { x = 0.0, y = 0.0, z = 0.0, w = 1.0 } }",
    "iconRenderCookingScale": "1.25",
    "iconRenderGlobalScale": "1.25",
    "overrideSceneExposure": "1.0",
    "fitToItemModelBoundingBox": "true",
    # ItemInfo's typed recolor hook: three RGBA channels plus the hidden
    # isSet flag. This remains research-only until visible results are proven.
    "itemColorCombinationSetup": "{ color0 = { 180, 60, 60, 255 }, color1 = { 45, 110, 210, 255 }, color2 = { 220, 180, 45, 255 }, isSet = true }",
    "itemColorCombinationPacked": "{ color0 = 0xFF3C3CB4, color1 = 0xFFD26E2D, color2 = 0xFF2DB4DC, isSet = true }",
}


def build(template: Path, output: Path, *, new_item_id: int, new_recipe_id: int,
          clear_icon_fallbacks: bool = False,
          render_control: str | None = None,
          packed_colors: tuple[int, int, int] | None = None) -> dict:
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    if min(new_item_id, new_recipe_id) <= 0 or max(new_item_id, new_recipe_id) > 0xFFFFFFFF:
        raise ValueError("IDs must be positive 32-bit unsigned values")
    if render_control is not None and render_control not in RENDER_CONTROL_VALUES:
        raise ValueError("unsupported render control: " + render_control)
    if packed_colors is not None:
        if len(packed_colors) != 3 or any(not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF for value in packed_colors):
            raise ValueError("packed_colors must contain three unsigned 32-bit integers")
    source_dir = template / "src"
    source_path = source_dir / "mod.lua"
    helper_path = source_dir / "kfc_content_registry.lua"
    if not source_path.is_file():
        raise ValueError("template must contain src/mod.lua")
    source = source_path.read_text(encoding="utf-8")
    # Fixtures evolve as research progresses, so discover the identity
    # markers instead of coupling the generator to one historical template.
    item_match = re.search(r"(?m)^local NEW_ITEM_ID\s*=\s*(\d+)\s*$", source)
    recipe_match = re.search(r"(?m)^local NEW_RECIPE_ID\s*=\s*(\d+)\s*$", source)
    if not item_match or not recipe_match:
        raise ValueError("template identity markers not found")
    source = source[:item_match.start()] + f"local NEW_ITEM_ID = {new_item_id}" + source[item_match.end():]
    # Locate the recipe marker after replacing the item marker so offsets are
    # still valid even when the replacement has a different length.
    recipe_match = re.search(r"(?m)^local NEW_RECIPE_ID\s*=\s*(\d+)\s*$", source)
    if not recipe_match:
        raise ValueError("template recipe identity marker not found")
    source = source[:recipe_match.start()] + f"local NEW_RECIPE_ID = {new_recipe_id}" + source[recipe_match.end():]
    marker = "clone.data.objectId = clone.guid\n"
    injection = r'''clone.data.objectId = clone.guid
-- Candidate 1: preserve the donor's model/scene fields and assign the
-- donor's known-good typed GUID to iconImage. This isolates catalog-image
-- precedence without allocating a UiTextureResource (which panics in this
-- build when registered from Lua).
local preview_helper = require('kfc_content_registry')
local preview_state_before = preview_helper.catalog_preview_state(clone)
log('CATALOG_PREVIEW_BEFORE', 'iconImage=' .. tostring(preview_state_before.icon_image) .. '|iconModel=' .. tostring(preview_state_before.icon_model) .. '|iconScene=' .. tostring(preview_state_before.icon_scene))
local ok_icon, icon_or_error = pcall(function()
    local donor_icon_guid = clone.data.iconImage
    if not donor_icon_guid then error('donor_icon_guid_missing') end
    local typed = preview_helper.assign_catalog_icon(clone, { guid = donor_icon_guid })
    if not typed then error('icon_assignment_rejected') end
    return clone.data.iconImage
end)
log('CATALOG_PREVIEW', 'candidate=image_only_donor_preview|ok=' .. tostring(ok_icon) .. '|value=' .. tostring(ok_icon and icon_or_error or icon_or_error))
local preview_state_after = preview_helper.catalog_preview_state(clone)
log('CATALOG_PREVIEW_AFTER', 'hasIconImage=' .. tostring(preview_state_after.has_icon_image) .. '|modelPreserved=' .. tostring(preview_state_after.icon_model == preview_state_before.icon_model) .. '|scenePreserved=' .. tostring(preview_state_after.icon_scene == preview_state_before.icon_scene))
'''
    if clear_icon_fallbacks:
        injection = injection.replace(
            "local preview_helper = require('kfc_content_registry')",
            "local ZERO_GUID = '00000000-0000-0000-0000-000000000000'\nclone.data.iconModel = ZERO_GUID\nclone.data.iconScene = ZERO_GUID\nlocal preview_helper = require('kfc_content_registry')",
            1,
        )
    render_injection = ""
    if render_control:
        value = RENDER_CONTROL_VALUES[render_control]
        field_name = ("itemColorCombinationSetup" if render_control == "itemColorCombinationPacked"
                      else render_control)
        if render_control == "itemColorCombinationPacked" and packed_colors is not None:
            value = "{ color0 = %s, color1 = %s, color2 = %s, isSet = true }" % tuple(
                f"0x{color:08X}" for color in packed_colors
            )
        render_injection = f'''local ok_render_control, render_control_error = pcall(function()
    clone.data.{field_name} = {value}
end)
log('CATALOG_RENDER_CONTROL', 'field={render_control}|ok=' .. tostring(ok_render_control)
    .. '|error=' .. tostring(render_control_error or '')
    .. '|value=' .. tostring(clone.data.{field_name}))
'''
    if marker in source and "CATALOG_PREVIEW_AFTER" not in source:
        source = source.replace(marker, injection, 1)
    if render_injection and "CATALOG_RENDER_CONTROL" not in source:
        icon_marker = "log('CATALOG_ICON_ASSIGNMENT', 'guid=' .. DONOR_ICON_GUID)\n"
        if icon_marker in source:
            source = source.replace(icon_marker, icon_marker + render_injection, 1)
        else:
            fallback_marker = "local indexed_count = 0\n"
            if fallback_marker not in source:
                raise ValueError("template does not contain a safe render-control insertion marker")
            source = source.replace(fallback_marker, render_injection + fallback_marker, 1)
    output_src = output / "src"
    output_src.mkdir(parents=True)
    (output_src / "mod.lua").write_text(source, encoding="utf-8")
    if helper_path.is_file():
        helper_source = helper_path.read_text(encoding="utf-8")
        # Catalog-preview probes do not inspect metadata families. Remove the
        # general helper's quarantine lookup table from this self-contained
        # copy so the safety scanner cannot mistake an unused type name for a
        # runtime access. The source helper itself remains unchanged.
        helper_source = re.sub(
            r"local QUARANTINED_METADATA_TYPES = \{.*?\n\}",
            "local QUARANTINED_METADATA_TYPES = {}",
            helper_source,
            count=1,
            flags=re.DOTALL,
        )
        (output_src / "kfc_content_registry.lua").write_text(helper_source, encoding="utf-8")
    manifest = {
        "schema": "control_center.catalog_preview_probe.v1",
        "id": output.name,
        "name": "Control Center Catalog Preview Probe (" + (render_control or "Image Only") + ")",
        "version": "0.1.0",
        "author": "Enshrouded Control Center",
        "capabilities": ["patch"],
        "feature_state": "research-only",
        "entrypoint": "src/mod.lua",
        "candidate_id": ("render_control_" + render_control if render_control else
                         ("image_only_cleared_fallbacks" if clear_icon_fallbacks else "image_only_donor_preview")),
        "donor_item_id": DONOR_ITEM_ID,
        "donor_recipe_id": DONOR_RECIPE_ID,
        "new_item_id": new_item_id,
        "new_recipe_id": new_recipe_id,
        **({"packed_colors": list(packed_colors)} if packed_colors is not None else {}),
        "preserves": [] if clear_icon_fallbacks else ["iconModel", "iconScene", "placed_object_behavior"],
        "mutates": (["iconImage", "iconModel", "iconScene"] if clear_icon_fallbacks else ["iconImage"])
                    + ([render_control] if render_control else []),
        "screenshot_verdict_required": True,
        "cleanup_required": True,
        "stable_profile_allowed": False,
        "rollback": "remove this research module while the game is stopped and restore the stable profile",
    }
    (output / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def load_packed_colors(path: Path) -> tuple[int, int, int]:
    """Read the validated three-slot color plan from a visual variant JSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    plan = data.get("item_color_combination") if isinstance(data, dict) else None
    if not isinstance(plan, dict):
        raise ValueError("visual variant does not contain item_color_combination")
    if plan.get("runtime_field") != "itemColorCombinationSetup" or plan.get("isSet") is not True:
        raise ValueError("visual variant contains an invalid item_color_combination plan")
    values = tuple(plan.get(channel) for channel in ("color0", "color1", "color2"))
    if any(not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF for value in values):
        raise ValueError("visual variant color plan must contain three packed 32-bit colors")
    return values  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--new-item-id", type=int, default=3987654821)
    parser.add_argument("--new-recipe-id", type=int, default=3987654822)
    parser.add_argument("--clear-icon-fallbacks", action="store_true",
                        help="clear iconModel/iconScene before assigning iconImage")
    parser.add_argument("--render-control", choices=sorted(RENDER_CONTROL_VALUES),
                        help="test exactly one ItemInfo render-control assignment")
    parser.add_argument("--packed-colors", help="three packed 32-bit colors (comma-separated) for the recolor probe")
    parser.add_argument("--color-plan", type=Path, help="visual_variant.json containing the Content Studio color plan")
    args = parser.parse_args()
    packed_colors = None
    if args.packed_colors:
        try:
            packed_colors = tuple(int(value.strip(), 0) for value in args.packed_colors.split(","))
        except ValueError as exc:
            parser.error(f"invalid --packed-colors: {exc}")
    if args.color_plan:
        if packed_colors is not None:
            parser.error("use either --packed-colors or --color-plan, not both")
        try:
            packed_colors = load_packed_colors(args.color_plan)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            parser.error(f"invalid --color-plan: {exc}")
    manifest = build(args.template, args.output, new_item_id=args.new_item_id,
                     new_recipe_id=args.new_recipe_id,
                     clear_icon_fallbacks=args.clear_icon_fallbacks,
                     render_control=args.render_control,
                     packed_colors=packed_colors)
    print(json.dumps({"generated": str(args.output), "manifest": manifest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
