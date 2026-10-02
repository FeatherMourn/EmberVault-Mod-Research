-- Read-only catalog trace for the vanilla bed and the attempted clone recipe.
local DONOR_RECIPE_ID = 3531872774
local CLONE_RECIPE_ID = 3987654322
local DONOR_ITEM_ID = 2940001508
local PREFIX = '[CC-CATALOG-TRACE] '
local function log(kind, ...) local a = {PREFIX .. kind}; for i=1,select('#',...) do a[#a+1]=tostring(select(i,...)) end; print(table.concat(a,'|')) end
local function resources(t)
    local ok, r = pcall(function() return game.assets.get_resources_by_type(t) or {} end)
    if not ok then log('ERROR', t, r); return {} end
    return r
end
local function entry_value(entry)
    if not entry then return nil end
    local ok, v = pcall(function() return entry.value or entry end)
    return ok and v or nil
end
local function recipe_output(recipe)
    for _, output in pairs(recipe and recipe.output or {}) do
        if output.item and output.item.value then return output.item.value end
    end
    return nil
end

log('BEGIN', 'donorRecipe=' .. DONOR_RECIPE_ID, 'cloneRecipe=' .. CLONE_RECIPE_ID)
local item_count, donor_items = 0, 0
for _, item in pairs(resources('keen::ItemInfo')) do
    item_count = item_count + 1
    if item.data and item.data.itemId and item.data.itemId.value == DONOR_ITEM_ID then donor_items = donor_items + 1 end
end
log('ITEMS', 'count=' .. item_count, 'donorMatches=' .. donor_items)

local registry_count, donor_recipe_count, clone_recipe_count = 0, 0, 0
for _, registry in pairs(resources('keen::RecipeRegistryResource')) do
    registry_count = registry_count + 1
    for index, recipe in pairs(registry.data and registry.data.recipes or {}) do
        local id = recipe.recipeId and recipe.recipeId.value
        if id == DONOR_RECIPE_ID then
            donor_recipe_count = donor_recipe_count + 1
            log('RECIPE', 'registry=' .. tostring(registry.guid), 'index=' .. index, 'id=' .. id, 'output=' .. tostring(recipe_output(recipe)))
        elseif id == CLONE_RECIPE_ID then
            clone_recipe_count = clone_recipe_count + 1
            log('CLONE_RECIPE', 'registry=' .. tostring(registry.guid), 'index=' .. index, 'id=' .. id, 'output=' .. tostring(recipe_output(recipe)))
        end
    end
end
log('RECIPE_COUNTS', 'registries=' .. registry_count, 'donor=' .. donor_recipe_count, 'clone=' .. clone_recipe_count)

local bundles, donor_entries, clone_entries = 0, 0, 0
for _, bundle in pairs(resources('keen::FbUiBundle')) do
    bundles = bundles + 1
    local trees = bundle.data and bundle.data.menu and bundle.data.menu.crafting
        and bundle.data.menu.crafting.recipes and bundle.data.menu.crafting.recipes.trees
    for ti, tree in pairs(trees or {}) do
        for gi, group in pairs(tree.groups or {}) do
            for si, set in pairs(group.sets or {}) do
                for ei, entry in pairs(set.entries or {}) do
                    local value = entry_value(entry)
                    if value == DONOR_RECIPE_ID or value == CLONE_RECIPE_ID then
                        if value == DONOR_RECIPE_ID then donor_entries = donor_entries + 1 else clone_entries = clone_entries + 1 end
                        log('MENU_ENTRY', 'bundle=' .. tostring(bundle.guid), 'tree=' .. ti, 'group=' .. gi, 'set=' .. si, 'entry=' .. ei, 'value=' .. tostring(value), 'entryType=' .. type(entry), 'valueType=' .. type(entry and entry.value))
                    end
                end
            end
        end
    end
end
log('MENU_COUNTS', 'bundles=' .. bundles, 'donorEntries=' .. donor_entries, 'cloneEntries=' .. clone_entries)
log('END', 'read_only=true')
return {}
