-- Reusable EML helper for registering runtime KFC content.
-- The caller supplies donor IDs and registry fields; this module never edits
-- the donor resource in place unless explicitly requested by the caller.
local M = {}

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

-- Clone a vanilla UI texture and point an ItemInfo clone at the new resource.
-- The item stores the texture resource GUID in iconImage; it does not store a
-- file path. The caller must pass the reflected UiTextureResource donor.
function M.clone_icon(item_resource, texture_donor)
    local texture_clone = M.clone_resource(texture_donor, 'keen::UiTextureResource')
    if not texture_clone then return nil end
    item_resource.data.iconImage = texture_clone.guid
    return texture_clone
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
