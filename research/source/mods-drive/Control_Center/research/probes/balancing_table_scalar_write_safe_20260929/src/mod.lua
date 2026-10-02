local PREFIX = '[CC-TUNING-SAFE-WRITE] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end

local ok, resources = pcall(function()
    return game.assets.get_resources_by_type('keen::BalancingTable') or {}
end)
log('RESOURCE_QUERY', 'ok=' .. tostring(ok) .. '|count=' .. tostring(ok and #resources or 0))

if ok and #resources > 0 then
    local resource = resources[1]
    local read_ok, original = pcall(function() return resource.data.baseCritChance end)
    log('ORIGINAL', 'ok=' .. tostring(read_ok) .. '|value=' .. tostring(read_ok and original or ''))
    if read_ok and type(original) == 'number' then
        local test_value = original + 0.125
        local write_ok, write_error = pcall(function() resource.data.baseCritChance = test_value end)
        local readback_ok, readback = pcall(function() return resource.data.baseCritChance end)
        log('WRITE', 'ok=' .. tostring(write_ok) .. '|error=' .. tostring(write_error or ''))
        log('READBACK', 'ok=' .. tostring(readback_ok) .. '|value=' .. tostring(readback or ''))
        local restore_ok, restore_error = pcall(function() resource.data.baseCritChance = original end)
        local restored_ok, restored = pcall(function() return resource.data.baseCritChance end)
        log('RESTORE', 'ok=' .. tostring(restore_ok) .. '|error=' .. tostring(restore_error or ''))
        log('RESTORED', 'ok=' .. tostring(restored_ok) .. '|value=' .. tostring(restored or ''))
    end
end
return {}
