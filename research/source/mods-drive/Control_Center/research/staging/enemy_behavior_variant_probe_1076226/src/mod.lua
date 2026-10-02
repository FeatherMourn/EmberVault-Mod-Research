-- Read-only mapped-variant access probe; no assignments and no pairs on wrappers.
local TYPE_NAME = 'keen::enemy::EnemyArsenalRegistryResource'
local PREFIX = '[CC-ENEMY-BEHAVIOR-VARIANT:enemy_behavior_variant_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function describe(value, label)
    local ok, text = pcall(function() return 'type=' .. type(value) .. '|text=' .. tostring(value) end)
    log('VALUE', label .. '|ok=' .. tostring(ok) .. '|' .. tostring(text))
end
local function inspect_payload(value, label)
    if value == nil then
        log('PAYLOAD', label .. '|nil=true')
        return
    end
    describe(value, label)
    local ok, iterator = pcall(function() return pairs(value) end)
    log('PAIRS', label .. '|ok=' .. tostring(ok) .. '|type=' .. type(iterator))
    if ok then
        local count = 0
        for key, child in iterator, value do
            count = count + 1
            if count <= 20 then describe(child, label .. '.' .. tostring(key)) end
        end
        log('FIELD_COUNT', label .. '|' .. tostring(count))
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
    local behavior
    for _, candidate in pairs(arsenal and arsenal.behaviors or {}) do behavior = candidate; break end
    local actions = behavior and behavior.actions
    if actions then
        local type_ok, variant_type = pcall(function() return actions.type end)
        log('VARIANT_TYPE', 'ok=' .. tostring(type_ok) .. '|value=' .. tostring(variant_type))
        local value_ok, variant_value = pcall(function() return actions.value end)
        log('VARIANT_VALUE', 'ok=' .. tostring(value_ok) .. '|type=' .. type(variant_value))
        if value_ok then inspect_payload(variant_value, 'behavior.actions.value') end
    else
        log('ACTIONS', 'missing=true')
    end
end
return {}
