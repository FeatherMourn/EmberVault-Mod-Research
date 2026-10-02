-- Bounded read-only progression dependency inventory. No assignments or writes.
local TYPES = {
    'keen::GameKnowledgeQueryResourceDb',
    'keen::GameKnowledgeQueryTriggerResource',
}
local PREFIX = '[CC-KNOWLEDGE-SCHEMA:knowledge_query_schema_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function shallow(value, label)
    local fields = 0
    for field, child in pairs(value or {}) do
        fields = fields + 1
        if fields <= 20 then log('FIELD', label .. '.' .. tostring(field) .. '|type=' .. type(child) .. '|text=' .. tostring(child)) end
    end
    log('FIELD_COUNT', label .. '|' .. fields)
end
for _, type_name in ipairs(TYPES) do
    local ok, resources = pcall(function() return game.assets.get_resources_by_type(type_name) or {} end)
    log('TYPE', type_name .. '|ok=' .. tostring(ok) .. '|type=' .. type(resources))
    if ok then
        local count = 0
        for key, resource in pairs(resources) do
            count = count + 1
            if count <= 2 then
                log('RESOURCE', type_name .. '|key=' .. tostring(key) .. '|guid=' .. tostring(resource and resource.guid))
                shallow(resource and resource.data, type_name)
            end
        end
        log('COUNT', type_name .. '|' .. count)
    end
end
log('RESULT', 'knowledge_schema_inventory_verified')
return {}
