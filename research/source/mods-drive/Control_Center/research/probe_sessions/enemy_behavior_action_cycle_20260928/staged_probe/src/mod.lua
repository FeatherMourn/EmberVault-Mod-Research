-- Read-only behavior action field inventory; no assignments.
local TYPE_NAME = 'keen::enemy::EnemyArsenalRegistryResource'
local PREFIX = '[CC-ENEMY-BEHAVIOR-ACTION:enemy_behavior_action_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function safe_text(value)
    local ok, result = pcall(function() return 'type=' .. type(value) .. '|text=' .. tostring(value) end)
    return ok, result
end
local function first(collection, label)
    local ok, item = pcall(function() for _, child in pairs(collection or {}) do return child end end)
    log('FIRST', label .. '|ok=' .. tostring(ok) .. '|type=' .. type(item))
    if not (ok and item) then return end
    local count = 0
    for key, child in pairs(item) do
        count = count + 1
        local read_ok, result = safe_text(child)
        if count <= 20 then
            log('FIELD', label .. '|key=' .. tostring(key) .. '|ok=' .. tostring(read_ok) .. '|' .. tostring(result))
            if read_ok then
                for _, nested in ipairs({'sequence', 'actionSequence', 'resource', 'guid', 'id', 'data'}) do
                    local nested_ok, nested_value = pcall(function() return child and child[nested] end)
                    if nested_ok and nested_value ~= nil then
                        local _, nested_text = safe_text(nested_value)
                        log('NESTED', label .. '.' .. tostring(key) .. '|key=' .. nested .. '|' .. tostring(nested_text))
                    end
                end
            end
        end
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
        local behavior
        for _, candidate in pairs(arsenal.behaviors or {}) do behavior = candidate; break end
        if behavior then first(behavior.actions, 'behavior.actions') end
    end
end
return {}
