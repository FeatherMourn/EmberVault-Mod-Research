-- Generated read-only gameplay schema enumeration probe.
local TYPE_NAME = 'keen::enemy::EnemyArsenalRegistryResource'
local PREFIX = '[CC-ENEMY-ARSENAL-ENUM] '
local function log(kind, value)
    print(PREFIX .. kind .. '|' .. tostring(value or ''))
end

log('API', 'resources=' .. type(game.assets and game.assets.get_resources_by_type))
local ok, resources = pcall(function()
    return game.assets.get_resources_by_type(TYPE_NAME) or {}
end)
log('RESULT', 'ok=' .. tostring(ok) .. '|type=' .. TYPE_NAME)
if ok then
    local count = 0
    for guid, resource in pairs(resources or {}) do
        count = count + 1
        if count <= 32 then
            log('ENTRY', 'key=' .. tostring(guid) .. '|value_type=' .. type(resource))
        end
    end
    log('COUNT', count)
end
return {}
