-- Validate the packaged mapped-variant safety contract; read-only.
local kfc = require('kfc_content_registry')
local TYPE_NAME = 'keen::enemy::EnemyArsenalRegistryResource'
local PREFIX = '[CC-ENEMY-BEHAVIOR-HELPER:enemy_behavior_helper_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
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
    local variant = kfc.read_mapped_variant(behavior and behavior.actions)
    log('VARIANT', 'available=' .. tostring(variant.available) .. '|type=' .. tostring(variant.variant_type) .. '|error=' .. tostring(variant.error))
    if variant.available then
        local iterator, state, initial, err = kfc.try_pairs(variant.payload)
        log('PAYLOAD_PAIRS', 'ok=' .. tostring(iterator ~= nil) .. '|error=' .. tostring(err) .. '|payload_type=' .. type(variant.payload))
        if iterator then
            local count = 0
            for key, value in iterator, state, initial do
                count = count + 1
                if count <= 12 then log('PAYLOAD_FIELD', tostring(key) .. '|type=' .. type(value)) end
            end
            log('PAYLOAD_COUNT', count)
        end
    end
end
return {}
