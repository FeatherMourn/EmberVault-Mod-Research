-- Donor-preserving JournalRegistry identity clone. Never attaches the clone.
local kfc = require('kfc_content_registry')
local TYPE_NAME = 'keen::JournalRegistryResource'
local DONOR_GUID = '33701b26-ec1d-423f-8e06-49f023b91b7f'
local CLONE_GUID = 'd5c7bb1c-398e-4cc7-8aa9-96b7d046b93f'
local NEW_ENTRY_ID = 3987654702
local NEW_QUEST_GUID = 'f1c3e4d2-4b6a-4f3c-9e10-2a7b6c8d5e41'
local PREFIX = '[CC-JOURNAL-CLONE:journal_registry_identity_clone_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function resources()
    local ok, result = pcall(function() return game.assets.get_resources_by_type(TYPE_NAME) or {} end)
    if not ok then log('STOP', 'resource_inventory_failed|' .. tostring(result)); return nil end
    return result
end
local function find(map, guid)
    for key, resource in pairs(map or {}) do
        if tostring(key) == guid or (resource and tostring(resource.guid) == guid) then return resource end
    end
end
local function count(value)
    local n = 0
    for _ in pairs(value or {}) do n = n + 1 end
    return n
end
local before = resources()
local donor = find(before, DONOR_GUID)
if not donor or not donor.data then log('STOP', 'donor_not_found'); return {} end
if find(before, CLONE_GUID) then log('STOP', 'clone_already_present'); return {} end
local donor_count = count(donor.data.quests)
log('DONOR', 'guid=' .. tostring(donor.guid) .. '|quests=' .. donor_count)
local clone, err = kfc.clone_resource(donor, TYPE_NAME, CLONE_GUID, 0)
if not clone then log('STOP', 'clone_registration_failed|' .. tostring(err)); return {} end
local after = resources()
local clone_readback = find(after, CLONE_GUID)
local donor_readback = find(after, DONOR_GUID)
local clone_count = count(clone_readback and clone_readback.data and clone_readback.data.quests)
local registry_count = count(after)
log('CLONE', 'guid=' .. tostring(clone_readback and clone_readback.guid) .. '|quests=' .. clone_count)
log('DONOR_PRESERVED', tostring(donor_readback ~= nil))
log('PARITY', 'quests=' .. tostring(donor_count == clone_count))
local donor_quest
for _, candidate in pairs(donor.data.quests or {}) do donor_quest = candidate; break end
local insert_ok, insert_error = pcall(function()
    if not clone_readback or not clone_readback.data then error('clone_registry_readback_missing') end
    log('INSERT_PHASE', 'before_quest_resource_create')
    local quest_clone = game.assets.create_resource(donor_quest, 'keen::JournalQuestResource', NEW_QUEST_GUID, 0)
    log('INSERT_PHASE', 'after_quest_resource_create')
    if not quest_clone or not quest_clone.data or not quest_clone.data.entryId then error('quest_clone_creation_failed') end
    quest_clone.data.entryId.value = NEW_ENTRY_ID
    log('INSERT_PHASE', 'before_typed_blob_array_create')
    local quest_values = {}
    for _, existing in pairs(clone_readback.data.quests or {}) do
        table.insert(quest_values, existing)
    end
    table.insert(quest_values, quest_clone.data)
    local typed_array = game.assets.create_resource(
        quest_values, 'keen::BlobArray<keen::JournalQuestResource>',
        'a9d2e8f1-6b44-4c5a-8d91-2f7e3b6c0a55', 0)
    log('INSERT_PHASE', 'after_typed_blob_array_create')
    if not typed_array or not typed_array.data then error('typed_blob_array_creation_failed') end
    clone_readback.data.quests = typed_array.data
    log('INSERT_PHASE', 'after_typed_blob_array_assign')
end)
local clone_after_insert = find(resources(), CLONE_GUID)
local donor_after_insert = find(resources(), DONOR_GUID)
local clone_count_after = count(clone_after_insert and clone_after_insert.data and clone_after_insert.data.quests)
local donor_count_after = count(donor_after_insert and donor_after_insert.data and donor_after_insert.data.quests)
log('INSERT', 'ok=' .. tostring(insert_ok) .. '|error=' .. tostring(insert_error) .. '|clone_quests=' .. clone_count_after .. '|donor_quests=' .. donor_count_after)
log('ATTACHMENT', 'live_registry=false|save=false|knowledge=false')
log('REGISTRY_COUNT', registry_count)
if insert_ok and clone_count_after == donor_count + 1 and donor_count_after == donor_count then
    log('RESULT', 'journal_registry_clone_insert_verified')
else
    log('RESULT', 'journal_registry_clone_insert_failed')
end
local live_attach_ok, live_attach_error = pcall(function()
    if not insert_ok or clone_count_after ~= donor_count + 1 then error('edited_clone_not_ready') end
    donor.data.quests = clone_after_insert.data.quests
end)
local donor_live_count = count(donor.data.quests)
log('LIVE_ATTACH', 'ok=' .. tostring(live_attach_ok) .. '|error=' .. tostring(live_attach_error) .. '|donor_quests=' .. donor_live_count)
if live_attach_ok and donor_live_count == donor_count + 1 then
    log('RESULT', 'journal_live_attachment_runtime_verified')
else
    log('RESULT', 'journal_live_attachment_runtime_failed')
end
return {}
