-- Read-only, shallow payload inspection. No assignments are performed.
local TYPE_NAME = 'keen::enemy::EnemyArsenalRegistryResource'
local PREFIX = '[CC-ENEMY-ARSENAL-READ] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function keys(value, label, limit)
    local ok, err = pcall(function()
        local count = 0
        for key, child in pairs(value or {}) do
            count = count + 1
            if count <= limit then log('FIELD', label .. '|key=' .. tostring(key) .. '|type=' .. type(child)) end
        end
        log('FIELD_COUNT', label .. '|' .. count)
    end)
    if not ok then log('FIELD_ERROR', label .. '|' .. tostring(err)) end
end

log('API', 'resources=' .. type(game.assets and game.assets.get_resources_by_type))
local ok, resources = pcall(function() return game.assets.get_resources_by_type(TYPE_NAME) or {} end)
log('RESULT', 'ok=' .. tostring(ok))
if ok then
    local first
    for _, resource in pairs(resources or {}) do first = resource; break end
    if first then
        local data_ok, data = pcall(function() return first.data end)
        log('DATA', 'ok=' .. tostring(data_ok) .. '|type=' .. type(data))
        if data_ok and data then
            keys(data, 'registry', 32)
            local arsenals_ok, arsenals = pcall(function() return data.arsenals end)
            log('ARSENALS', 'ok=' .. tostring(arsenals_ok) .. '|type=' .. type(arsenals))
            if arsenals_ok and arsenals then
                local count = 0
                for _, arsenal in pairs(arsenals) do
                    count = count + 1
                    if count <= 4 then keys(arsenal, 'arsenal_' .. count, 32) end
                end
                log('ARSENAL_COUNT', count)
            end
        end
    end
end
return {}
