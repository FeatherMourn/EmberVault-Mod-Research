"""Build a research-only registered furniture clone with a model substitution."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("new_item_id", type=int)
    parser.add_argument("new_recipe_id", type=int)
    parser.add_argument("replacement_model_guid")
    parser.add_argument("--material-guid")
    parser.add_argument("--texture-guid")
    parser.add_argument("--color")
    args = parser.parse_args()
    if args.new_item_id <= 0 or args.new_recipe_id <= 0:
        parser.error("new IDs must be positive")
    if not args.replacement_model_guid.strip():
        parser.error("replacement_model_guid is required")
    if args.color and not re.fullmatch(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?", args.color.strip()):
        parser.error("color must use #RRGGBB or #RRGGBBAA")
    template_path = args.template / "src" / "mod.lua" if args.template.is_dir() else args.template
    source = template_path.read_text(encoding="utf-8")
    source, item_replacements = re.subn(
        r"local NEW_ITEM_ID = \d+", f"local NEW_ITEM_ID = {args.new_item_id}", source, count=1
    )
    source, recipe_replacements = re.subn(
        r"local NEW_RECIPE_ID = \d+", f"local NEW_RECIPE_ID = {args.new_recipe_id}", source, count=1
    )
    if item_replacements != 1 or recipe_replacements != 1:
        raise SystemExit("template does not contain numeric identity markers")
    marker = "local clone = clone_or_error\n"
    has_existing_model_assignment = "local replacement_model_guid" in source
    injection = marker
    if not has_existing_model_assignment:
        injection += f'''local replacement_model_guid = {json.dumps(args.replacement_model_guid.strip())}
local original_model = clone.data.iconModel
local original_model_guid = original_model and original_model.guid or original_model and original_model.value or original_model
if tostring(original_model_guid or '') == replacement_model_guid then
    log('STOP', 'replacement_equals_donor')
    return {{}}
end
local ok_model, model_error = pcall(function()
    clone.data.iconModel = replacement_model_guid
end)
log('VISUAL_ASSIGNMENT', 'ok=' .. tostring(ok_model) .. '|error=' .. tostring(model_error or '')
    .. '|before=' .. tostring(original_model and original_model.guid or original_model and original_model.value or original_model or 'nil')
    .. '|after=' .. tostring(clone.data.iconModel and clone.data.iconModel.guid or clone.data.iconModel and clone.data.iconModel.value or clone.data.iconModel or 'nil'))
'''
    for field, value in (("material", args.material_guid), ("texture", args.texture_guid), ("color", args.color)):
        if value and value.strip():
            injection += f'''local ok_{field}, error_{field} = pcall(function()
    clone.data.{field} = {json.dumps(value.strip())}
end)
log('VISUAL_{field.upper()}_ASSIGNMENT', 'ok=' .. tostring(ok_{field}) .. '|error=' .. tostring(error_{field} or '') .. '|value=' .. tostring(clone.data.{field} or 'nil'))
'''
    if marker not in source:
        raise SystemExit("template does not contain the proven clone marker")
    source = source.replace(marker, injection, 1)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "src").mkdir()
    (args.output / "src" / "mod.lua").write_text(source, encoding="utf-8")
    manifest = {
        "id": args.output.name,
        "name": "Control Center Registered Visual Substitution Probe",
        "version": "0.1.0",
        "author": "Enshrouded Control Center",
        "capabilities": ["patch"],
        "feature_state": "research-only",
        "entrypoint": "src/mod.lua",
        "mode": "registered_clone_visual_assignment",
        "runtime_mutation": True,
        "research_only": True,
        "new_item_id": args.new_item_id,
        "new_recipe_id": args.new_recipe_id,
        "replacement_model_guid": args.replacement_model_guid.strip(),
        "replacement_material_guid": args.material_guid.strip() if args.material_guid else None,
        "replacement_texture_guid": args.texture_guid.strip() if args.texture_guid else None,
        "replacement_color": args.color.strip() if args.color else None,
        "rollback": "remove this module while the game is stopped",
    }
    (args.output / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated registered visual substitution probe: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
