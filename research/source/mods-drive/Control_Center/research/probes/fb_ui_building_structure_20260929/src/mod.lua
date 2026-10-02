local PREFIX = '[CC-FBUI-STRUCTURE] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function keys(value, label, depth)
    if depth > 2 or type(value) ~= 'table' then return end
    local count = 0
    for key, child in pairs(value) do
        count = count + 1
        log('FIELD', label .. '.' .. tostring(key) .. '|lua_type=' .. type(child))
    end
    log('COUNT', label .. '|count=' .. count)
end
local ok, bundles = pcall(function() return game.assets.get_resources_by_type('keen::FbUiBundle') or {} end)
if not ok then log('WARNING', 'resource_lookup_failed'); return {} end
log('BUNDLES', #bundles)
for index, bundle in pairs(bundles) do
    local data = bundle.data
    log('BUNDLE', index .. '|guid=' .. tostring(bundle.guid))
    keys(data, 'bundle', 0)
    keys(data and data.menu, 'menu', 1)
    keys(data and data.menu and data.menu.building, 'menu.building', 1)
    keys(data and data.menu and data.menu.crafting, 'menu.crafting', 1)
end
log('WARNING', 'read_only_structure_only')
return {}
