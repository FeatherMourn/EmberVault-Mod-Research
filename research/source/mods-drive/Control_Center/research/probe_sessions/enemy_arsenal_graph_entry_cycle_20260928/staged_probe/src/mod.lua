-- Read-only inspection of one attack and one behavior graph entry.
local TYPE_NAME = 'keen::enemy::EnemyArsenalRegistryResource'
local PREFIX = '[CC-ENEMY-ARSENAL-GRAPH:enemy_arsenal_graph_entry_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function inspect_one(collection, label)
    local ok, entry = pcall(function()
        for _, child in pairs(collection or {}) do return child end
        return nil
    end)
    log('FIRST', label .. '|ok=' .. tostring(ok) .. '|type=' .. type(entry))
    if ok and entry then
        local field_ok, count = pcall(function()
            local n = 0
            for key, child in pairs(entry) do
                n = n + 1
                if n <= 32 then log('FIELD', label .. '|key=' .. tostring(key) .. '|type=' .. type(child)) end
            end
            return n
        end)
        log('FIELD_COUNT', label .. '|ok=' .. tostring(field_ok) .. '|count=' .. tostring(count))
    end
end

local ok, resources = pcall(function() return game.assets.get_resources_by_type(TYPE_NAME) or {} end)
log('RESULT', 'ok=' .. tostring(ok))
if ok then
    local resource
    for _, candidate in pairs(resources or {}) do resource = candidate; break end
    local data_ok, data = pcall(function() return resource and resource.data end)
    log('DATA', 'ok=' .. tostring(data_ok) .. '|type=' .. type(data))
    local arsenal
    if data_ok and data and data.arsenals then
        for _, candidate in pairs(data.arsenals) do arsenal = candidate; break end
    end
    log('ARSENAL', 'type=' .. type(arsenal))
    if arsenal then
        inspect_one(arsenal.attacks, 'attacks')
        inspect_one(arsenal.behaviors, 'behaviors')
    end
end
return {}
