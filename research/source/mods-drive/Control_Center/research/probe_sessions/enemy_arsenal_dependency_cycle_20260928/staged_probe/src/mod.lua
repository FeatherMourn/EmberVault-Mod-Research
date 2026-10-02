-- Read-only nested dependency identity inventory; no assignments.
local TYPE_NAME = 'keen::enemy::EnemyArsenalRegistryResource'
local PREFIX = '[CC-ENEMY-ARSENAL-DEPS:enemy_arsenal_dependency_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function describe(value, label)
    local ok, summary = pcall(function()
        local parts = {'type=' .. type(value), 'text=' .. tostring(value)}
        for _, key in ipairs({'guid', 'id', 'data', 'reference', 'resource'}) do
            local read_ok, child = pcall(function() return value and value[key] end)
            if read_ok and child ~= nil then parts[#parts + 1] = key .. '=' .. tostring(child) .. ':' .. type(child) end
        end
        return table.concat(parts, '|')
    end)
    log('VALUE', label .. '|ok=' .. tostring(ok) .. '|' .. tostring(summary))
end
local function first(collection, label)
    local ok, item = pcall(function() for _, child in pairs(collection or {}) do return child end end)
    log('FIRST', label .. '|ok=' .. tostring(ok) .. '|type=' .. type(item))
    if ok and item then
        local count = 0
        for key, child in pairs(item) do
            count = count + 1
            if count <= 16 then describe(child, label .. '.' .. tostring(key)) end
        end
        log('FIELD_COUNT', label .. '|' .. count)
    end
end
local ok, resources = pcall(function() return game.assets.get_resources_by_type(TYPE_NAME) or {} end)
log('RESULT', 'ok=' .. tostring(ok))
if ok then
    local resource
    for _, candidate in pairs(resources or {}) do resource = candidate; break end
    local data = resource and resource.data
    local arsenal
    for _, candidate in pairs(data and data.arsenals or {}) do arsenal = candidate; break end
    if arsenal then
        first(arsenal.attacks, 'attacks')
        first(arsenal.behaviors, 'behaviors')
    end
end
return {}
