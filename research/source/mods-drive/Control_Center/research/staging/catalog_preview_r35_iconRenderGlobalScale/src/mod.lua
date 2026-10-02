-- Controlled furniture clone experiment.
-- This never edits the vanilla donor; it creates independent ItemInfo/recipe records.
local DONOR_ID = 2940001508
local NEW_ITEM_ID = 3901120422
local NEW_RECIPE_ID = 3901120423
local PREFIX = '[CC-BED-CLONE] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end

local function resources(type_name)
    local ok, result = pcall(function() return game.assets.get_resources_by_type(type_name) or {} end)
    if not ok then log('ERROR', type_name .. '|' .. tostring(result)); return {} end
    return result
end

local function find_item(id)
    for _, item in pairs(resources('keen::ItemInfo')) do
        if item and item.data and item.data.itemId and item.data.itemId.value == id then return item end
    end
    return nil
end

local function find_registry(type_name, field)
    for _, resource in pairs(resources(type_name)) do
        if resource and resource.data and resource.data[field] then return resource end
    end
    return nil
end

local function deep_copy(value, seen)
    if type(value) ~= 'table' then return value end
    seen = seen or {}
    if seen[value] then return seen[value] end
    local result = {}
    seen[value] = result
    for key, child in pairs(value) do result[deep_copy(key, seen)] = deep_copy(child, seen) end
    return result
end

local donor = find_item(DONOR_ID)
if not donor then log('STOP', 'donor_not_found'); return {} end
local item_registry = find_registry('keen::ItemRegistryResource', 'itemRefs')
local recipe_registry = find_registry('keen::RecipeRegistryResource', 'recipes')
if not item_registry or not recipe_registry then
    log('STOP', 'required_registry_missing'); return {}
end

for _, ref in pairs(item_registry.data.itemRefs) do
    if ref and ref.data and ref.data.itemId and ref.data.itemId.value == NEW_ITEM_ID then
        log('EXISTING', 'item_already_registered'); return {}
    end
end
for _, recipe in pairs(recipe_registry.data.recipes) do
    if recipe and recipe.recipeId and recipe.recipeId.value == NEW_RECIPE_ID then
        log('EXISTING', 'recipe_already_registered'); return {}
    end
end

local ok_item, clone_or_error = pcall(function()
    return game.assets.register_resource(donor.data, 'keen::ItemInfo')
end)
if not ok_item or not clone_or_error then log('STOP', 'item_clone_failed|' .. tostring(clone_or_error)); return {} end
local clone = clone_or_error
local replacement_model_guid = "4c7f1c3a-b448-4460-ad5e-a79b3859d2c1"
local original_model = clone.data.iconModel
local ok_model, model_error = pcall(function()
    clone.data.iconModel = replacement_model_guid
end)
log('VISUAL_ASSIGNMENT', 'ok=' .. tostring(ok_model) .. '|error=' .. tostring(model_error or '')
    .. '|before=' .. tostring(original_model and original_model.guid or original_model and original_model.value or original_model or 'nil')
    .. '|after=' .. tostring(clone.data.iconModel and clone.data.iconModel.guid or clone.data.iconModel and clone.data.iconModel.value or clone.data.iconModel or 'nil'))
clone.data.itemId.value = NEW_ITEM_ID
clone.data.debugName = 'CC_Custom_Bed_001'
local function ref_value(value)
    if type(value) == 'table' then
        return tostring(value.guid or value.value or value.data or value)
    end
    return tostring(value or 'nil')
end
log('CATALOG_PREVIEW_BEFORE', 'iconImage=' .. ref_value(clone.data.iconImage)
    .. '|iconModel=' .. ref_value(clone.data.iconModel)
    .. '|iconScene=' .. ref_value(clone.data.iconScene))
-- Use an existing localized bed label until custom localization payloads are
-- supported; the item identity and recipe remain independent.
clone.data.name = '5ea4b496-9073-4c41-9c68-9c9a990b7378'
log('DISPLAY_FIELDS', 'name=' .. tostring(clone.data.name) .. '|caption=' .. tostring(clone.data.caption) .. '|description=' .. tostring(clone.data.description))
-- Keep the cloned ItemInfo identity internally consistent. The donor's
-- objectId points back to the vanilla item and can cause catalog de-duplication.
clone.data.objectId = clone.guid
-- Known-good vanilla UiTextureResource recovered for the current build.
-- This probe isolates catalog icon consumption from model substitution.
local DONOR_ICON_GUID = 'b7eb722c-ed5d-48d8-93c8-a68f6ef342d0'
clone.data.iconImage = DONOR_ICON_GUID
log('CATALOG_ICON_ASSIGNMENT', 'guid=' .. DONOR_ICON_GUID)
log('CATALOG_PREVIEW_AFTER', 'iconImage=' .. ref_value(clone.data.iconImage)
    .. '|iconModel=' .. ref_value(clone.data.iconModel)
    .. '|iconScene=' .. ref_value(clone.data.iconScene))
local indexed_count = 0
for _ in pairs(resources('keen::ItemInfo')) do indexed_count = indexed_count + 1 end
log('INDEXED_ITEMS_AFTER_CREATE', indexed_count)
local discovered_clone = find_item(NEW_ITEM_ID)
log('DISCOVERED_CLONE', tostring(discovered_clone ~= nil))

local donor_recipe
for _, recipe in pairs(recipe_registry.data.recipes) do
    if recipe.output then
        for _, output in pairs(recipe.output) do
            if output.item and output.item.value == DONOR_ID then donor_recipe = recipe; break end
        end
    end
    if donor_recipe then break end
end
if not donor_recipe then log('STOP', 'donor_recipe_not_found'); return {} end

local new_recipe = deep_copy(donor_recipe)
new_recipe.recipeId.value = NEW_RECIPE_ID
new_recipe.debugName = 'CC_Custom_Bed_001_Recipe'
for _, output in pairs(new_recipe.output or {}) do
    if output.item then output.item.value = NEW_ITEM_ID end
    if output.itemRef then output.itemRef = clone.guid end
end

local item_before = #item_registry.data.itemRefs
local recipe_before = #recipe_registry.data.recipes
table.insert(item_registry.data.itemRefs, clone)
-- ItemRegistryResource keeps dbgNames positionally parallel to itemRefs.
-- Leaving this array short makes the engine reject the appended item during
-- catalog construction even though the Lua table visibly contains the clone.
if item_registry.data.dbgNames then
    table.insert(item_registry.data.dbgNames, clone.data.debugName)
    log('DBG_NAMES', 'count=' .. #item_registry.data.dbgNames)
else
    log('DBG_NAMES', 'missing')
end
table.insert(recipe_registry.data.recipes, new_recipe)
log('REGISTERED', 'itemId=' .. NEW_ITEM_ID .. '|recipeId=' .. NEW_RECIPE_ID)
log('COUNTS', 'items=' .. item_before .. '->' .. #item_registry.data.itemRefs .. '|recipes=' .. recipe_before .. '->' .. #recipe_registry.data.recipes)
log('PLACED_ENTITY', tostring(clone.data.equipment and clone.data.equipment.placedEntity))
log('IDENTITY', 'guid=' .. tostring(clone.guid) .. '|objectId=' .. tostring(clone.data.objectId))
local item_knowledge_links = 0
for _, knowledge_resource in pairs(resources('keen::ItemKnowledgeResource')) do
    local array = knowledge_resource.data and knowledge_resource.data.knowledgeArray
    for _, record in pairs(array or {}) do
        if record.itemId and record.itemId.value == DONOR_ID then
            local already = false
            for _, existing in pairs(array) do
                if existing.itemId and existing.itemId.value == NEW_ITEM_ID then already = true end
            end
            if not already then
                local knowledge_clone = deep_copy(record)
                knowledge_clone.itemId.value = NEW_ITEM_ID
                table.insert(array, knowledge_clone)
                item_knowledge_links = item_knowledge_links + 1
            end
        end
    end
end
log('ITEM_KNOWLEDGE_LINKS', item_knowledge_links)
-- Preserve the native HashKey32 entry wrapper. A plain Lua number is rejected
-- by the typed UI entry array.
local ui_links = 0
local ui_sets = 0
local ok_hash, hash_candidate = pcall(function()
    return game.assets.create_resource({ value = NEW_RECIPE_ID }, 'keen::HashKey32')
end)
log('HASH_FACTORY', 'ok=' .. tostring(ok_hash) .. '|value=' .. tostring(hash_candidate) .. '|type=' .. type(hash_candidate) .. '|dataValue=' .. tostring(ok_hash and hash_candidate.data and hash_candidate.data.value))
for _, bundle in pairs(resources('keen::FbUiBundle')) do
    local trees = bundle.data and bundle.data.menu and bundle.data.menu.crafting
        and bundle.data.menu.crafting.recipes and bundle.data.menu.crafting.recipes.trees
    for _, tree in pairs(trees or {}) do
        for _, group in pairs(tree.groups or {}) do
            for _, set in pairs(group.sets or {}) do
                for entry_index, entry in pairs(set.entries or {}) do
                    local value = entry and (entry.value or entry)
                    if value == 3531872774 then
                        ui_sets = ui_sets + 1
                        log('UI_SET_BEFORE', 'entries=' .. tostring(#(set.entries or {})) .. '|index=' .. tostring(entry_index) .. '|sets=' .. tostring(#(group.sets or {})))
                        local ok_link, err_link = pcall(function()
                            if not ok_hash or not hash_candidate.data then error('hash_factory_missing_data') end
                            local cloned_set = deep_copy(set)
                            cloned_set.entries[entry_index] = hash_candidate.data
                            table.insert(group.sets, cloned_set)
                            log('UI_SET_AFTER', 'entries=' .. tostring(#(cloned_set.entries or {})) .. '|index=' .. tostring(entry_index) .. '|value=' .. tostring(cloned_set.entries[entry_index] and cloned_set.entries[entry_index].value) .. '|sets=' .. tostring(#(group.sets or {})))
                        end)
                        if ok_link then ui_links = ui_links + 1
                        else log('UI_LINK_ERROR', tostring(err_link)) end
                    end
                end
            end
        end
    end
end
log('UI_LINKS', ui_links .. '|matching_sets=' .. ui_sets)
log('WARNING', 'menu_visibility_and_save_persistence_require_in_game_validation')
return {}
