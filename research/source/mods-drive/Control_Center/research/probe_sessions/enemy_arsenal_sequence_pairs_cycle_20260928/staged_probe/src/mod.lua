-- Read-only attack action and sequence dependency inventory; no assignments.
local TYPE_NAME = 'keen::enemy::EnemyArsenalRegistryResource'
local PREFIX = '[CC-ENEMY-ARSENAL-SEQ:enemy_arsenal_sequence_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function read(value, label)
    local ok, result = pcall(function()
        return 'type=' .. type(value) .. '|text=' .. tostring(value)
    end)
    log('VALUE', label .. '|ok=' .. tostring(ok) .. '|' .. tostring(result))
end
local function inspect_first(collection, label)
    local ok, item = pcall(function()
        for _, child in pairs(collection or {}) do return child end
    end)
    log('FIRST', label .. '|ok=' .. tostring(ok) .. '|type=' .. type(item))
    if not (ok and item) then return end
    local count = 0
    for key, child in pairs(item) do
        count = count + 1
        if count <= 12 then read(child, label .. '.' .. tostring(key)) end
    end
    log('FIELD_COUNT', label .. '|' .. tostring(count))
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
        local attack
        for _, candidate in pairs(arsenal.attacks or {}) do attack = candidate; break end
        if attack then
            log('ATTACK', 'ok=true|type=' .. type(attack))
            inspect_first(attack.actions, 'attack.actions')
            inspect_first(attack.commands, 'attack.commands')
        end
        local behavior
        for _, candidate in pairs(arsenal.behaviors or {}) do behavior = candidate; break end
        if behavior then
            log('BEHAVIOR', 'ok=true|type=' .. type(behavior))
            inspect_first(behavior.actions, 'behavior.actions')
        end
    end
end
return {}
