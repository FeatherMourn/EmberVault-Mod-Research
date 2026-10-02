"""Generate a research-only probe for independent recipe customization."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--new-item-id", type=int, default=3987654801)
    parser.add_argument("--new-recipe-id", type=int, default=3987654802)
    parser.add_argument("--replacement-workshop-id", type=int, default=1302892403)
    parser.add_argument("--knowledge-donor-recipe-id", type=int, default=0,
                        help="optional populated recipe query to copy onto the clone")
    args = parser.parse_args()
    if min(args.new_item_id, args.new_recipe_id) <= 0:
        parser.error("IDs must be positive")
    source_path = args.template / "src" / "mod.lua" if args.template.is_dir() else args.template
    source = source_path.read_text(encoding="utf-8")
    replacements = {
        "local NEW_ITEM_ID = 3987654321": f"local NEW_ITEM_ID = {args.new_item_id}",
        "local NEW_RECIPE_ID = 3987654322": f"local NEW_RECIPE_ID = {args.new_recipe_id}",
    }
    for old, new in replacements.items():
        if old not in source:
            raise SystemExit(f"template marker not found: {old}")
        source = source.replace(old, new)
    marker = "local new_recipe = deep_copy(donor_recipe)\nnew_recipe.recipeId.value = NEW_RECIPE_ID\n"
    injection = "local recipe_helper = require('kfc_content_registry')\nlocal new_recipe, recipe_clone_error = recipe_helper.clone_recipe_for_edit(donor_recipe)\nif not new_recipe then log('STOP', 'bounded_recipe_clone_failed|' .. tostring(recipe_clone_error)); return {} end\nnew_recipe.recipeId.value = NEW_RECIPE_ID\nlocal KNOWLEDGE_DONOR_RECIPE_ID = %d\nif KNOWLEDGE_DONOR_RECIPE_ID > 0 then\n    local requirement_donor\n    for _, candidate in pairs(recipe_registry.data and recipe_registry.data.recipes or {}) do\n        if candidate.recipeId and candidate.recipeId.value == KNOWLEDGE_DONOR_RECIPE_ID then requirement_donor = candidate; break end\n    end\n    if not requirement_donor then log('RECIPE_EDIT', 'knowledgeRequirement_replace|ok=false|value=donor_not_found')\n    else\n        local replaced, replace_error = recipe_helper.replace_knowledge_requirement(new_recipe, requirement_donor)\n        if replaced then new_recipe = replaced; log('RECIPE_EDIT', 'knowledgeRequirement_replace|ok=true|value=' .. tostring(KNOWLEDGE_DONOR_RECIPE_ID))\n        else log('RECIPE_EDIT', 'knowledgeRequirement_replace|ok=false|value=' .. tostring(replace_error)) end\n    end\nend\n" % args.knowledge_donor_recipe_id + r'''-- Research-only independent recipe customization attempts.
local function attempt_recipe_edit(label, fn)
    local ok, value = pcall(fn)
    log('RECIPE_EDIT', label .. '|ok=' .. tostring(ok) .. '|value=' .. tostring(ok and value or value))
end
attempt_recipe_edit('craftingDuration', function()
    if new_recipe.craftingDuration == nil then error('field_missing') end
    new_recipe.craftingDuration = 1
    return new_recipe.craftingDuration
end)
attempt_recipe_edit('output_count', function()
    if not new_recipe.output or not new_recipe.output[1] then error('output_missing') end
    if new_recipe.output[1].count == nil then error('count_field_missing') end
    new_recipe.output[1].count = 2
    return new_recipe.output[1].count
end)
attempt_recipe_edit('input_item_stack_count', function()
    if not new_recipe.input or not new_recipe.input[1] then error('input_missing') end
    local stack = new_recipe.input[1].itemStack
    if not stack or stack.count == nil then error('item_stack_count_missing') end
    stack.count = 1
    return stack.count
end)
attempt_recipe_edit('workshopId', function()
    if new_recipe.workshopId == nil then error('field_missing') end
    local typed = game.assets.create_resource({ value = %d }, 'keen::HashKey32')
    if not typed or not typed.data then error('typed_hash_factory_missing') end
    new_recipe.workshopId = typed.data
    return new_recipe.workshopId.value
end)
attempt_recipe_edit('requiredProps_clear', function()
    if new_recipe.requiredProps == nil then error('field_missing') end
    new_recipe.requiredProps = {}
    return 'cleared_on_clone'
end)
attempt_recipe_edit('knowledgeRequirement_clear', function()
    if new_recipe.knowledgeRequirement == nil then error('field_missing') end
    new_recipe.knowledgeRequirement = nil
    return 'cleared_on_clone'
end)
''' % args.replacement_workshop_id
    if marker not in source:
        raise SystemExit("recipe identity marker not found")
    source = source.replace(marker, injection, 1)
    if args.output.exists():
        raise SystemExit(f"output already exists: {args.output}")
    (args.output / "src").mkdir(parents=True)
    (args.output / "src" / "mod.lua").write_text(source, encoding="utf-8")
    helper = Path(__file__).resolve().parents[1] / "research" / "runtime" / "kfc_content_registry.lua"
    (args.output / "src" / "kfc_content_registry.lua").write_text(helper.read_text(encoding="utf-8"), encoding="utf-8")
    manifest = {
        "schema": "control_center.recipe_customization_probe.v1",
        "id": args.output.name,
        "name": "Control Center Recipe Customization Probe",
        "version": "0.1.0",
        "author": "Enshrouded Control Center",
        "capabilities": ["patch"],
        "feature_state": "research-only",
        "entrypoint": "src/mod.lua",
        "new_item_id": args.new_item_id,
        "new_recipe_id": args.new_recipe_id,
        "replacement_workshop_id": args.replacement_workshop_id,
        "knowledge_donor_recipe_id": args.knowledge_donor_recipe_id or None,
        "edits": ["craftingDuration", "output[1].count", "input[1].itemStack.count", "workshopId", "requiredProps", "knowledgeRequirement"],
        "rollback": "remove this module while the game is stopped and restore the stable profile"
    }
    (args.output / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated recipe customization probe: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
