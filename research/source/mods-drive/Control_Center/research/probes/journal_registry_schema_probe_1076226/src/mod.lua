-- Bounded read-only quest/journal schema inventory. No assignments or writes.
local TYPE_NAME = 'keen::JournalRegistryResource'
local PREFIX = '[CC-JOURNAL-SCHEMA:journal_registry_schema_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function value_type(value)
    local ok, result = pcall(function() return type(value) .. '|' .. tostring(value) end)
    return ok and result or ('error|' .. tostring(result))
end
local ok, resources = pcall(function() return game.assets.get_resources_by_type(TYPE_NAME) or {} end)
log('RESULT', 'ok=' .. tostring(ok) .. '|type=' .. type(resources))
if not ok then return {} end
local resource_count = 0
for key, resource in pairs(resources) do
    resource_count = resource_count + 1
    if resource_count <= 3 then
        log('RESOURCE', 'key=' .. tostring(key) .. '|guid=' .. tostring(resource and resource.guid))
        local data = resource and resource.data
        local fields = 0
        for field, value in pairs(data or {}) do
            fields = fields + 1
            if fields <= 24 then log('FIELD', tostring(field) .. '|value=' .. value_type(value)) end
        end
        log('FIELD_COUNT', fields)
        local quests = data and data.quests
        local quest_count = 0
        for quest_key, quest in pairs(quests or {}) do
            quest_count = quest_count + 1
            if quest_count <= 3 then
                log('QUEST', 'key=' .. tostring(quest_key) .. '|type=' .. value_type(quest))
                local quest_fields = 0
                for field, value in pairs(quest or {}) do
                    quest_fields = quest_fields + 1
                    if quest_fields <= 20 then log('QUEST_FIELD', tostring(field) .. '|value=' .. value_type(value)) end
                end
                log('QUEST_FIELD_COUNT', quest_fields)
            end
        end
        log('QUEST_COUNT', quest_count)
    end
end
log('RESOURCE_COUNT', resource_count)
return {}
