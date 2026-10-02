-- Bounded read-only inspection of action-sequence resources.
local TYPE_NAME = 'keen::actor::ActionSequence'
local PREFIX = '[CC-ACTION-SEQUENCE-RESOURCE:enemy_action_sequence_resource_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function render(value)
    local ok, text = pcall(function() return 'type=' .. type(value) .. '|text=' .. tostring(value) end)
    return ok, text
end
local ok, resources = pcall(function() return game.assets.get_resources_by_type(TYPE_NAME) or {} end)
log('RESULT', 'ok=' .. tostring(ok) .. '|type=' .. type(resources))
if ok then
    local count = 0
    for key, resource in pairs(resources) do
        count = count + 1
        if count <= 8 then
            local data = resource and resource.data
            local data_ok, data_text = render(data)
            log('RESOURCE', 'key=' .. tostring(key) .. '|data_ok=' .. tostring(data_ok) .. '|' .. tostring(data_text))
            if data then
                local fields = 0
                for field, value in pairs(data) do
                    fields = fields + 1
                    if fields <= 20 then
                        local field_ok, field_text = render(value)
                        log('FIELD', 'key=' .. tostring(key) .. '|field=' .. tostring(field) .. '|ok=' .. tostring(field_ok) .. '|' .. tostring(field_text))
                    end
                end
                log('FIELD_COUNT', 'key=' .. tostring(key) .. '|' .. tostring(fields))
            end
        end
    end
    log('COUNT', tostring(count))
end
return {}
