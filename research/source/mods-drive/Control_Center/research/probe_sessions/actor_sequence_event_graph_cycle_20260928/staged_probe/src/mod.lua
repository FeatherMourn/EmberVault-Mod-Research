-- Bounded read-only inspection of action-sequence resources.
local TYPE_NAME = 'keen::actor::ActorSequenceResource'
local TARGET_GUID = 'a837f190-d163-4ef5-a48e-3ea7caac7296'
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
    local matched = false
    for key, resource in pairs(resources) do
        count = count + 1
        local data = resource and resource.data
        if data and data.resourceId == TARGET_GUID then
            matched = true
            log('MATCH', 'key=' .. tostring(key) .. '|resourceId=' .. tostring(data.resourceId))
            local sequence
            for _, candidate in pairs(data.subSequences or {}) do sequence = candidate; break end
            if sequence then
                local sequence_ok, sequence_text = render(sequence)
                log('SEQUENCE', 'ok=' .. tostring(sequence_ok) .. '|' .. tostring(sequence_text))
                local event
                for _, candidate in pairs(sequence.events or {}) do event = candidate; break end
                if event then
                    local event_ok, event_text = render(event)
                    log('EVENT', 'ok=' .. tostring(event_ok) .. '|' .. tostring(event_text))
                    local ok_type, event_type = pcall(function() return event.type end)
                    local ok_value, event_value = pcall(function() return event.value end)
                    log('EVENT_FIELDS', 'type_ok=' .. tostring(ok_type) .. '|type=' .. tostring(event_type) .. '|value_ok=' .. tostring(ok_value) .. '|value_type=' .. type(event_value))
                end
                local event_count = 0
                for index, candidate in pairs(sequence.events or {}) do
                    event_count = event_count + 1
                    if event_count <= 64 then
                        local candidate_type = pcall(function() return candidate.type end) and candidate.type or nil
                        local candidate_value = candidate.value
                        local field_names = {}
                        if candidate_value then
                            for field, _ in pairs(candidate_value) do
                                field_names[#field_names + 1] = tostring(field)
                            end
                        end
                        log('EVENT_TYPE', 'index=' .. tostring(index) .. '|type=' .. tostring(candidate_type) .. '|fields=' .. table.concat(field_names, ','))
                    end
                end
                log('EVENT_COUNT', tostring(event_count))
            end
        elseif count <= 8 then
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
    log('MATCH_COUNT', matched and '1' or '0')
end
return {}
