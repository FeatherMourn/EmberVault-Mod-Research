-- Donor-preserving identity clone probe.
-- Registers one new ActorSequenceResource and verifies readback only.
-- It deliberately does not attach the clone to an attack or enemy.
local TYPE_NAME = 'keen::actor::ActorSequenceResource'
local DONOR_GUID = 'a837f190-d163-4ef5-a48e-3ea7caac7296'
local CLONE_GUID = 'c8f7a8a3-6f6f-4ae9-b15e-30fd2c5c7e11'
local PREFIX = '[CC-ACTOR-SEQUENCE-CLONE:actor_sequence_identity_clone_1076226] '

local function log(kind, value)
    print(PREFIX .. kind .. '|' .. tostring(value or ''))
end

log('START', 'probe_loaded')
local ok_helper, kfc_or_error = pcall(function() return require('kfc_content_registry') end)
if not ok_helper then
    log('STOP', 'helper_load_failed|' .. tostring(kfc_or_error))
    return {}
end
local kfc = kfc_or_error
log('HELPER', 'loaded')

local function resource_map()
    local ok, result = pcall(function()
        return game.assets.get_resources_by_type(TYPE_NAME) or {}
    end)
    if not ok then
        log('STOP', 'resource_inventory_failed|' .. tostring(result))
        return nil
    end
    return result
end

local function find_by_guid(resources, guid)
    for key, resource in pairs(resources or {}) do
        if tostring(key) == guid or (resource and tostring(resource.guid) == guid) then
            return resource
        end
    end
    return nil
end

local function event_signature(data)
    local sequence_count = 0
    local event_count = 0
    local types = {}
    for _, sequence in pairs(data and data.subSequences or {}) do
        sequence_count = sequence_count + 1
        for index, event in pairs(sequence.events or {}) do
            event_count = event_count + 1
            types[tostring(index) .. '=' .. tostring(event and event.type)] = true
        end
    end
    local ordered = {}
    for value in pairs(types) do table.insert(ordered, value) end
    table.sort(ordered)
    return sequence_count, event_count, table.concat(ordered, ',')
end

local before = resource_map()
if not before then return {} end
local donor = find_by_guid(before, DONOR_GUID)
if not donor or not donor.data then
    log('STOP', 'donor_not_found')
    return {}
end
local existing = find_by_guid(before, CLONE_GUID)
if existing then
    log('STOP', 'clone_already_present')
    return {}
end

local donor_sequences, donor_events, donor_types = event_signature(donor.data)
log('DONOR', 'guid=' .. tostring(donor.guid) .. '|sequences=' .. donor_sequences .. '|events=' .. donor_events)

local clone, err = kfc.clone_resource(donor, TYPE_NAME, CLONE_GUID, 0)
if not clone then
    log('STOP', 'clone_registration_failed|' .. tostring(err))
    return {}
end

local id_write_ok, id_write_error = pcall(function()
    clone.data.resourceId = CLONE_GUID
end)
log('CLONE_ID_WRITE', 'ok=' .. tostring(id_write_ok) .. '|error=' .. tostring(id_write_error))

local after = resource_map()
local clone_readback = find_by_guid(after, CLONE_GUID)
local donor_readback = find_by_guid(after, DONOR_GUID)
if not clone_readback or not clone_readback.data then
    log('STOP', 'clone_readback_missing')
    return {}
end

local clone_sequences, clone_events, clone_types = event_signature(clone_readback.data)
log('CLONE', 'guid=' .. tostring(clone_readback.guid) .. '|resourceId=' .. tostring(clone_readback.data.resourceId) .. '|sequences=' .. clone_sequences .. '|events=' .. clone_events)
log('DONOR_PRESERVED', tostring(donor_readback ~= nil))
log('PARITY', 'sequences=' .. tostring(donor_sequences == clone_sequences) .. '|events=' .. tostring(donor_events == clone_events) .. '|types=' .. tostring(donor_types == clone_types))
local attach_ok, attach_error = pcall(function()
    local arsenal_type = 'keen::enemy::EnemyArsenalRegistryResource'
    local arsenals = game.assets.get_resources_by_type(arsenal_type) or {}
    for _, arsenal_resource in pairs(arsenals) do
        for _, arsenal in pairs(arsenal_resource.data and arsenal_resource.data.arsenals or {}) do
            for attack_key, attack in pairs(arsenal.attacks or {}) do
                local description = attack and attack.description
                if description and description.actionSequence == DONOR_GUID then
                    local before_sequence = description.actionSequence
                    description.actionSequence = CLONE_GUID
                    log('ATTACHMENT', 'arsenal=' .. tostring(arsenal_resource.guid) .. '|attack=' .. tostring(attack_key) .. '|before=' .. tostring(before_sequence) .. '|after=' .. tostring(description.actionSequence))
                    return
                end
            end
        end
    end
    error('donor_attack_with_target_sequence_not_found')
end)
log('ATTACHMENT_RESULT', 'ok=' .. tostring(attach_ok) .. '|error=' .. tostring(attach_error))
log('RESULT', 'identity_clone_and_attack_attachment_tested')
return {}
