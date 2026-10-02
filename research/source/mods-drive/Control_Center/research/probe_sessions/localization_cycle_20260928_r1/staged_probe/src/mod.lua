local registry = require('kfc_localization_registry')
local DONOR_ID = 2940001508
local NEW_ID = 3987654701
local PREFIX = '[CC-LOCALIZATION-ITEM-TRANSITION] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function resources(type_name)
    local ok, result = pcall(function() return game.assets.get_resources_by_type(type_name) or {} end)
    if not ok then log('ERROR', type_name .. '|' .. tostring(result)); return {} end
    return result
end
local function find_item(id)
    for _, item in pairs(resources('keen::ItemInfo')) do
        if item and item.data and item.data.itemId and item.data.itemId.value == id then return item end
    end
end
local function attempt(label, fn)
    local ok, result = pcall(fn)
    log(label, 'ok=' .. tostring(ok) .. '|result=' .. tostring(ok and result or result))
    return ok, result
end
log('START', 'begin')
local tag_ok, tag = attempt('TAG', function()
    return registry.register_tag('Control Center Transition Probe', 'Transition probe')
end)
if not tag_ok then return {} end
local collection_ok, collection = attempt('COLLECTION', function()
    return registry.register({['Control Center Transition Probe'] = {En_Us = 'Control Center Transition Probe'}}, '8b1e4f67-2a9d-5c30-b8e1-4d7f6a2c9014', 'En_Us', {'En_Us'})
end)
if not collection_ok then return {} end
log('BEFORE_ITEM_LOOKUP', 'collection_complete=true')
local donor = find_item(DONOR_ID)
log('DONOR_LOOKUP', 'found=' .. tostring(donor ~= nil))
if not donor then return {} end
local clone_ok, clone = attempt('ITEM_CLONE', function()
    return game.assets.register_resource(donor.data, 'keen::ItemInfo')
end)
if not clone_ok or not clone then return {} end
attempt('ITEM_ID_MUTATION', function() clone.data.itemId.value = NEW_ID; return clone.data.itemId.value end)
attempt('DEBUG_NAME_MUTATION', function() clone.data.debugName = 'CC_Localization_Transition_Bed'; return clone.data.debugName end)
attempt('NAME_MUTATION', function() clone.data.name = tag.guid; return clone.data.name end)
attempt('DESCRIPTION_MUTATION', function() clone.data.description = tag.guid; return clone.data.description end)
attempt('OBJECT_ID_MUTATION', function() clone.data.objectId = clone.guid; return clone.data.objectId end)
log('END', 'completed')
return {}
