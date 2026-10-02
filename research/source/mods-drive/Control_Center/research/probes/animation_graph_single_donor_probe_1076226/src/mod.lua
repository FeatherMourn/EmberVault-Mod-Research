-- One-resource payload boundary probe. No mutation, registration, or attachment.
local PREFIX = '[CC-ANIMATION-GRAPH-DONOR:animation_graph_single_donor_probe_1076226] '
local TYPE = 'keen::anim_graph::runtime_graph::AnimationGraphResource2_0'
local GUID = '0022fed6-0380-4125-be31-ba8b5fdcbfcd'
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function read(label, callback)
    local ok, value = pcall(callback)
    log('FIELD', label .. '|ok=' .. tostring(ok) .. '|value=' .. tostring(value))
    return ok, value
end

log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|read_only=true')
log('PHASE', 'before_resource_lookup')
local ok, resource = pcall(function() return game.assets.get_resource(GUID, TYPE, 0) end)
log('PHASE', 'after_resource_lookup|ok=' .. tostring(ok) .. '|found=' .. tostring(resource ~= nil))
if not ok or not resource then
    log('RESULT', 'resource_lookup_failed|' .. tostring(resource))
    return {}
end
read('guid', function() return resource.guid end)
log('PHASE', 'before_payload_read')
local data_ok, data = pcall(function() return resource.data end)
log('PHASE', 'after_payload_read|ok=' .. tostring(data_ok) .. '|type=' .. type(data))
if not data_ok or not data then
    log('RESULT', 'payload_read_failed|' .. tostring(data))
    return {}
end
read('hierarchy', function() return data.hierarchy end)
read('nodeDefinitions_count', function() return #data.nodeDefinitions end)
read('slotBoneIndexMapping_count', function() return #data.slotBoneIndexMapping end)
read('usedInputIds', function() return data.usedInputIds end)
read('rootNode', function() return data.rootNode end)
read('postProcessRootNode', function() return data.postProcessRootNode end)
log('ATTACHMENT', 'animation=false|entity=false|world=false|save=false')
log('RESULT', 'single_animation_graph_payload_read_complete')
log('END', 'build=1076226')
return {}
