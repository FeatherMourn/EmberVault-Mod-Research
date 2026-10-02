-- Controlled furniture clone experiment.
-- This never edits the vanilla donor; it creates independent ItemInfo/recipe records.
local DONOR_ID = 2940001508
local DONOR_RECIPE_ID = 3531872774
local DONOR_GUID = '01474f79-6b5a-4bcd-999d-7e9339fda91c'
local NEW_ITEM_ID = 3987654341
local NEW_RECIPE_ID = 3987654342
local NEW_RECIPE_GUID = 'd5e8a3c1-4f69-7b12-0e35-9c8d6a2f4273'
local DONOR_ICON_GUID = 'b7eb722c-ed5d-48d8-93c8-a68f6ef342d0'
local PREFIX = '[CC-DONOR-ICON-BED] '
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
-- Cache the donor recipe before registering any new resources. Registration
-- can change the runtime indexes used by later resource enumeration.
local donor_recipe_cached
for _, recipe in pairs(recipe_registry.data.recipes or {}) do
    local matches_donor = recipe and recipe.recipeId and recipe.recipeId.value == DONOR_RECIPE_ID
    for _, output in pairs(recipe and recipe.output or {}) do
        if output and output.item and output.item.value == DONOR_ID then matches_donor = true end
        if output and output.itemRef and tostring(output.itemRef) == DONOR_GUID then matches_donor = true end
    end
    if matches_donor then
        donor_recipe_cached = recipe
        break
    end
end
if not donor_recipe_cached then
    -- Live-KFC mode may expose a registry variant without the donor recipe
    -- indexed in its first snapshot. Continue to the broader typed/output
    -- matching search below instead of failing prematurely.
    log('INFO', 'donor_recipe_not_cached_trying_fallback')
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

local localization = require('kfc_localization_registry')
local LOCALIZATION_KEY = 'Control Center Combined Localized Bed'
local tag_ok, tag = pcall(function()
    return localization.register_tag(LOCALIZATION_KEY, 'Atomic localization test bed')
end)
log('LOCALIZATION_TAG', 'ok=' .. tostring(tag_ok) .. '|result=' .. tostring(tag_ok and tag and tag.guid or tag))
local collection_ok, collection = pcall(function()
    return localization.register({[LOCALIZATION_KEY] = {En_Us = 'Control Center Combined Localized Bed'}}, '9d0a2a4f-3b7b-5e4c-9aa2-6b8e5f77c1d0', 'En_Us')
end)
log('LOCALIZATION_COLLECTION', 'ok=' .. tostring(collection_ok) .. '|result=' .. tostring(collection_ok and collection and collection.guid or collection))
local ok_item, clone_or_error = pcall(function()
    return game.assets.register_resource(donor.data, 'keen::ItemInfo')
end)
if not ok_item or not clone_or_error then log('STOP', 'item_clone_failed|' .. tostring(clone_or_error)); return {} end
local clone = clone_or_error
clone.data.itemId.value = NEW_ITEM_ID
clone.data.debugName = 'CC_Combined_Localized_Bed'
-- The exported ItemInfo iconImage is a GUID reference to a
-- keen::UiTextureResource. Clone the vanilla texture so this probe tests the
-- full reference path without importing new binary image data yet.
local icon_donor
for _, texture in pairs(resources('keen::UiTextureResource')) do
    if texture and tostring(texture.guid) == DONOR_ICON_GUID then icon_donor = texture; break end
end
if not icon_donor then log('STOP', 'icon_donor_not_found|' .. DONOR_ICON_GUID); return {} end
local icon_ok, icon_clone = pcall(function()
    return game.assets.register_resource(icon_donor.data, 'keen::UiTextureResource')
end)
if not icon_ok or not icon_clone then log('STOP', 'icon_clone_failed|' .. tostring(icon_clone)); return {} end
clone.data.iconImage = icon_clone.guid
log('ICON_CLONE', 'source=' .. DONOR_ICON_GUID .. '|new=' .. tostring(icon_clone.guid))
-- The custom tag is paired with a matching locale-collection entry.
-- The item identity and recipe remain independent of the donor IDs.
if tag_ok and tag then
    -- The runtime tag registers successfully, but build 1076226 does not
    -- resolve a same-startup custom LocaTag through ItemInfo.name. Keep the
    -- donor name for the stable rendered fixture; localization registration
    -- remains available as a separately verified runtime capability.
    clone.data.name = donor.data.name
    clone.data.caption = donor.data.caption
    clone.data.description = donor.data.description
else
    clone.data.name = '5ea4b496-9073-4c41-9c68-9c9a990b7378'
end
log('DISPLAY_FIELDS', 'name=' .. tostring(clone.data.name) .. '|caption=' .. tostring(clone.data.caption) .. '|description=' .. tostring(clone.data.description))
-- Keep the cloned ItemInfo identity internally consistent. The donor's
-- objectId points back to the vanilla item and can cause catalog de-duplication.
clone.data.objectId = clone.guid
local indexed_count = 0
for _ in pairs(resources('keen::ItemInfo')) do indexed_count = indexed_count + 1 end
log('INDEXED_ITEMS_AFTER_CREATE', indexed_count)
local discovered_clone = find_item(NEW_ITEM_ID)
log('DISCOVERED_CLONE', tostring(discovered_clone ~= nil))

local donor_recipe = donor_recipe_cached
local function recipe_matches(recipe)
    if recipe and recipe.recipeId and recipe.recipeId.value == DONOR_RECIPE_ID then return true end
    for _, output in pairs(recipe and recipe.output or {}) do
        if output and output.item and output.item.value == DONOR_ID then return true end
        if output and output.itemRef and output.itemRef.value == DONOR_ID then return true end
        if output and output.itemRef and tostring(output.itemRef) == DONOR_GUID then return true end
    end
    return false
end
for _, candidate_type in ipairs({'keen::RecipeRegistryResource', 'keen::ds::RecipeRegistryResource'}) do
    for _, candidate_registry in pairs(resources(candidate_type)) do
        for _, recipe in pairs(candidate_registry.data and candidate_registry.data.recipes or {}) do
            if recipe_matches(recipe) then
                donor_recipe = recipe
                recipe_registry = candidate_registry
                break
            end
        end
        if donor_recipe then break end
    end
    if donor_recipe then break end
end
if not donor_recipe then log('STOP', 'donor_recipe_not_found'); return {} end

local new_recipe = deep_copy(donor_recipe)
new_recipe.recipeGuid = NEW_RECIPE_GUID
new_recipe.recipeId.value = NEW_RECIPE_ID
log('RECIPE_IDENTITY', 'guid=' .. tostring(new_recipe.recipeGuid) .. '|id=' .. tostring(new_recipe.recipeId and new_recipe.recipeId.value))
new_recipe.debugName = 'CC_Combined_Localized_Bed_Recipe'
-- The new localization tag remains registered for later research, but using
-- it here makes the recipe display fall back to the donor in the same startup
-- pass. Keep the recipe label known-resolvable for this rendering probe.
new_recipe.recipeName = donor_recipe.recipeName
for _, requirement in ipairs({new_recipe.knowledgeRequirement, new_recipe.completionRequirementQuery}) do
    if requirement and requirement.type == 'Extern' and requirement.knowledgeOrQueryId then
        requirement.knowledgeOrQueryId.value = 0
        requirement.compareValue = 0
    end
end
-- Keep the donor's typed requirement fields intact until a schema-safe empty
-- requirement representation is identified. Assigning nil to these typed
-- fields can cross the Lua/Rust boundary as an invalid resource value.
for _, output in pairs(new_recipe.output or {}) do
    if output.item then output.item.value = NEW_ITEM_ID end
    if output.itemRef then output.itemRef = clone.guid end
end
local first_output = new_recipe.output and new_recipe.output[1]
log('OUTPUT_MAPPING', 'item=' .. tostring(first_output and first_output.item and first_output.item.value)
    .. '|itemRef=' .. tostring(first_output and first_output.itemRef))
log('VISUAL_FIELDS', 'iconModel=' .. tostring(clone.data.iconModel)
    .. '|iconScene=' .. tostring(clone.data.iconScene)
    .. '|placedEntity=' .. tostring(clone.data.equipment and clone.data.equipment.placedEntity))

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
