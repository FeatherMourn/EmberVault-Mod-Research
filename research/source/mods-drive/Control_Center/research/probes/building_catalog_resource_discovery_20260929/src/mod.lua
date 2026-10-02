local PREFIX = '[CC-BUILD-CATALOG-DISCOVERY] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end

-- Type enumeration is build-sensitive and has stalled the loader on this
-- route. Keep discovery read-only and use known qualified names; metadata
-- lookup accepts strings directly.
local candidates = {
    'keen::VoxelBlueprintConfig',
    'keen::VoxelBlueprintItemRegistryResource',
    'keen::VoxelBlueprintMaterialPoolRegistryResource',
    'keen::FbUiBundle',
    'keen::ItemRegistryResource',
    'keen::RecipeRegistryResource',
}
for _, type_name in ipairs(candidates) do
    local metadata_ok, rows = pcall(function()
        return game.assets.get_resource_metadata_by_type(type_name, 8) or {}
    end)
    local count = 0
    local guids = {}
    for _, row in ipairs(rows or {}) do
        count = count + 1
        guids[#guids + 1] = tostring(row.guid or '')
    end
    log('TYPE|' .. type_name .. '|ok=' .. tostring(metadata_ok) .. '|count=' .. tostring(count) .. '|guids=' .. table.concat(guids, ','))
end
return {}
