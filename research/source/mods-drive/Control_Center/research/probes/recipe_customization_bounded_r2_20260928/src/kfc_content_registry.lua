-- Reusable EML helper for registering runtime KFC content.
-- The caller supplies donor IDs and registry fields; this module never edits
-- the donor resource in place unless explicitly requested by the caller.
local M = {}

-- Known blocking descriptor families are quarantined from normal helper use.
-- Dedicated research probes may still test them, but production workflows
-- must fail fast instead of stalling a live session.
local QUARANTINED_METADATA_TYPES = {
    ['keen::TemplateResource'] = true,
}

local function copy(value, seen)
    if type(value) ~= 'table' then return value end
    seen = seen or {}
    if seen[value] then return seen[value] end
    local out = {}
    seen[value] = out
    for k, v in pairs(value) do out[copy(k, seen)] = copy(v, seen) end
    return out
end

function M.resources(type_name)
    return game.assets.get_resources_by_type(type_name) or {}
end

-- Compatibility wrapper for loader builds that do not yet expose the
-- metadata-only API. This never falls back to descriptor decoding: callers
-- receive an explicit unavailable result instead of an unsafe guess.
function M.resource_metadata_by_type(type_name)
    if QUARANTINED_METADATA_TYPES[type_name] then
        return { available = false, rows = {}, error = 'type_quarantined:' .. tostring(type_name) }
    end
    if not game.assets or type(game.assets.get_resource_metadata_by_type) ~= 'function' then
        return { available = false, rows = {}, error = 'metadata_api_unavailable' }
    end
    local ok, rows = pcall(function()
        return game.assets.get_resource_metadata_by_type(type_name) or {}
    end)
    if not ok then
        return { available = false, rows = {}, error = tostring(rows) }
    end
    return { available = true, rows = rows, error = nil }
end

function M.find_by_value(type_name, field, value)
    for _, resource in pairs(M.resources(type_name)) do
        local data = resource and resource.data
        local field_value = data and data[field]
        if field_value and field_value.value == value then return resource end
    end
end

function M.clone_resource(donor, type_name)
    return game.assets.register_resource(donor.data, type_name)
end

-- Copy only the reflected RecipeInfo fields used by the current build. This
-- avoids recursively walking opaque/cyclic typed descriptor graphs.
function M.clone_recipe_for_edit(recipe)
    local recipe_type = type(recipe)
    if recipe_type ~= 'table' and recipe_type ~= 'userdata' then return nil, 'recipe_must_be_table_or_userdata' end
    local out = {}
    for _, field in ipairs({
        'recipeGuid', 'recipeId', 'workshopGuid', 'workshopId',
        'craftingDuration', 'requiredProps', 'debugName',
        'showIsImportantLabel',
    }) do
        local ok, value = pcall(function() return recipe[field] end)
        if ok and value ~= nil then out[field] = value end
    end
    for _, field in ipairs({'input', 'output'}) do
        local ok_field, source = pcall(function() return recipe[field] end)
        if not ok_field then return nil, 'recipe_field_read_failed:' .. field end
        if source ~= nil then
            out[field] = {}
            local count = 0
            local ok_pairs, pair_error = pcall(function()
              for index, value in pairs(source) do
                count = count + 1
                if count > 128 then return nil, 'recipe_array_too_large:' .. field end
                out[field][index] = copy(value)
              end
            end)
            if not ok_pairs then return nil, 'recipe_array_read_failed:' .. field .. ':' .. tostring(pair_error) end
        end
    end
    return out, nil
end

-- Apply validated, donor-independent recipe edits to a bounded clone.
-- This is deliberately an authoring primitive: the caller must append the
-- returned recipe with a new recipeId and verify craftability in-game.
-- Unknown fields are rejected instead of being guessed against a new build.
function M.edit_recipe(recipe, changes)
    if type(recipe) ~= 'table' or type(changes) ~= 'table' then
        return nil, 'recipe_and_changes_must_be_tables'
    end
    local allowed = {
        debugName = true, craftTime = true, craftingDuration = true,
        ingredients = true, input = true, output = true,
        station = true, amount = true,
        knowledgeRequirement = true,
    }
    for field, _ in pairs(changes) do
        if not allowed[field] then return nil, 'unsupported_recipe_field:' .. tostring(field) end
    end
    local edited, clone_error = M.clone_recipe_for_edit(recipe)
    if not edited then return nil, clone_error end
    for field, value in pairs(changes) do
        if field == 'craftTime' or field == 'craftingDuration' then
            if type(value) ~= 'number' or value < 0 then return nil, 'invalid_craft_time' end
        elseif field == 'amount' then
            if type(value) ~= 'number' or value <= 0 then return nil, 'invalid_output_amount' end
        elseif field == 'ingredients' or field == 'input' or field == 'output' then
            if type(value) ~= 'table' then return nil, 'invalid_recipe_array:' .. field end
        end
        edited[field] = copy(value)
    end
    return edited, nil
end

-- Clone a vanilla UI texture and point an ItemInfo clone at the new resource.
-- The item stores the texture resource GUID in iconImage; it does not store a
-- file path. The caller must pass the reflected UiTextureResource donor.
function M.clone_icon(item_resource, texture_donor)
    local texture_clone = M.clone_resource(texture_donor, 'keen::UiTextureResource')
    if not texture_clone then return nil end
    item_resource.data.iconImage = texture_clone.guid
    return texture_clone
end

-- Return the fields that control the catalog preview without touching the item.
-- This is intentionally diagnostic: iconImage takes precedence over the model
-- and scene fallbacks, so a placed object can work while its catalog tile is
-- blank. Keeping the three values together makes that distinction observable.
function M.catalog_preview_state(item_resource)
    local data = item_resource and item_resource.data or {}
    return {
        icon_image = data.iconImage,
        icon_model = data.iconModel,
        icon_scene = data.iconScene,
        has_icon_image = data.iconImage ~= nil,
        has_icon_model = data.iconModel ~= nil,
        has_icon_scene = data.iconScene ~= nil,
    }
end

-- Assign a known-good texture reference to an ItemInfo clone. The reference
-- must be the typed GUID of a UiTextureResource already accepted by the
-- current build; arbitrary file paths and plain Lua tables are not valid.
function M.assign_catalog_icon(item_resource, texture_resource)
    if not item_resource or not item_resource.data then
        return false, 'item_resource_missing'
    end
    if not texture_resource or not texture_resource.guid then
        return false, 'texture_resource_guid_missing'
    end
    item_resource.data.iconImage = texture_resource.guid
    return true, nil
end

-- Research-only PNG import path. EML decodes ordinary image data, encodes it
-- into a GPU texture format, and creates immutable content for the new
-- UiTextureResource. The donor supplies the build-specific resource schema;
-- the caller must still validate the result in-game before shipping it.
function M.import_png_icon(item_resource, texture_donor, png_path, format_name)
    if not image or not io or not game.assets.create_content then
        error('EML image/content APIs are unavailable')
    end
    local png = io.read(png_path)
    local decoded = image.decode(png)
    local format = format_name or 'R8G8B8A8_unorm'
    local texture_buffer = image.encode_texture(decoded, format)
    local content = game.assets.create_content(texture_buffer)
    local texture_clone = M.clone_resource(texture_donor, 'keen::UiTextureResource')
    if not texture_clone then return nil end
    texture_clone.data.data = content
    texture_clone.data.size.x = decoded.width
    texture_clone.data.size.y = decoded.height
    texture_clone.data.format = format
    texture_clone.data.type = 'Texture2D'
    texture_clone.data.levelCount = 1
    texture_clone.data.isTiled = false
    item_resource.data.iconImage = texture_clone.guid
    return texture_clone
end

function M.append_registry(registry, field, value)
    table.insert(registry.data[field], value)
end

-- FbUiBundle recipe entries use typed fixed-size arrays. Do not append to
-- set.entries. Clone the containing set, replace the donor HashKey32 entry,
-- then append the cloned set to group.sets.
function M.clone_recipe_set(bundle, donor_recipe_id, new_recipe_id)
    local trees = bundle.data.menu.crafting.recipes.trees
    for _, tree in pairs(trees or {}) do
        for _, group in pairs(tree.groups or {}) do
            for _, set in pairs(group.sets or {}) do
                for index, entry in pairs(set.entries or {}) do
                    local value = entry and (entry.value or entry)
                    if value == donor_recipe_id then
                        local cloned = copy(set)
                        local typed_id = game.assets.create_resource(
                            { value = new_recipe_id }, 'keen::HashKey32')
                        cloned.entries[index] = typed_id.data
                        table.insert(group.sets, cloned)
                        return true
                    end
                end
            end
        end
    end
    return false
end

M.deep_copy = copy
return M
