-- Probe standalone typed quest creation only. It never attaches the result.
local TYPE_NAME = 'keen::JournalRegistryResource'
local QUEST_TYPE = 'keen::JournalQuestResource'
local PREFIX = '[CC-JOURNAL-QUEST-CREATE:journal_quest_resource_create_probe_1076226] '
local NEW_GUID = 'e7d6d3a5-9708-47c7-8c7d-78b2a3c88d41'
local NEW_ENTRY_ID = 3987654701
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local ok, resources = pcall(function() return game.assets.get_resources_by_type(TYPE_NAME) or {} end)
if not ok then log('STOP', 'registry_inventory_failed|' .. tostring(resources)); return {} end
local donor
for _, resource in pairs(resources) do donor = resource; break end
local quest
for _, candidate in pairs(donor and donor.data and donor.data.quests or {}) do quest = candidate; break end
if not quest then log('STOP', 'quest_donor_not_found'); return {} end
log('DONOR', 'type=' .. type(quest) .. '|text=' .. tostring(quest))
local create_ok, created_or_error = pcall(function()
    return game.assets.create_resource(quest, QUEST_TYPE, NEW_GUID, 0)
end)
log('CREATE', 'ok=' .. tostring(create_ok) .. '|type=' .. type(created_or_error) .. '|value=' .. tostring(created_or_error))
if create_ok and created_or_error then
    local data = created_or_error.data
    local donor_entry_id = quest.entryId and quest.entryId.value
    local edit_ok, edit_error = pcall(function()
        if not data or not data.entryId then error('created_entry_id_missing') end
        data.entryId.value = NEW_ENTRY_ID
    end)
    log('EDIT', 'ok=' .. tostring(edit_ok) .. '|error=' .. tostring(edit_error) .. '|new_entry_id=' .. tostring(data and data.entryId and data.entryId.value))
    log('READBACK', 'guid=' .. tostring(created_or_error.guid) .. '|data_type=' .. type(data) .. '|entryId=' .. tostring(data and data.entryId and data.entryId.value))
    log('DONOR_IDENTITY_PRESERVED', tostring(quest.entryId and quest.entryId.value == donor_entry_id))
    log('ATTACHMENT', 'registry=false|save=false|knowledge=false')
    log('RESULT', 'standalone_quest_resource_created')
else
    log('RESULT', 'standalone_quest_resource_create_failed')
end
return {}
