local PREFIX = '[CC-TUNING-SAFE-BATCH] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local fields = {'baseCritChance', 'damageMod2Handed', 'comfortSetup'}
local ok, resources = pcall(function() return game.assets.get_resources_by_type('keen::BalancingTable') or {} end)
log('RESOURCE_QUERY', 'ok=' .. tostring(ok) .. '|count=' .. tostring(ok and #resources or 0))
if ok then
    for _, resource in pairs(resources) do
        for _, field in ipairs(fields) do
            local read_ok, value = pcall(function() return resource.data[field] end)
            log('FIELD', field .. '|ok=' .. tostring(read_ok) .. '|type=' .. tostring(read_ok and type(value) or value) .. '|value=' .. tostring(read_ok and value or ''))
        end
    end
end
return {}
