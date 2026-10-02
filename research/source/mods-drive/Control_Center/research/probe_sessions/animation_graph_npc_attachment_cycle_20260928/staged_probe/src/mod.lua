-- Attach an exact-parity graph clone to one NPC collection entry only.
local GRAPH_TYPE = 'keen::anim_graph::runtime_graph::AnimationGraphResource2_0'
local DONOR_GUID = '0022fed6-0380-4125-be31-ba8b5fdcbfcd'
local CLONE_GUID = '7d3109de-80a7-44ad-a549-680460153d46'
local OWNER_TYPE = 'keen::NpcCollection'
local OWNER_GUID = '377f61dc-c7b8-4e4f-830f-7d2c3e8b7fd8'
local OWNER_NAME = 'NPC_Workshop_Hunter01'
local PREFIX = '[CC-ANIMATION-NPC-ATTACH:animation_graph_npc_attachment_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function safe(callback) local ok, value = pcall(callback); if ok then return value end; return nil end

log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|owner=' .. OWNER_NAME)
local donor = safe(function() return game.assets.get_resource(DONOR_GUID, GRAPH_TYPE, 0) end)
if not donor or not donor.data then log('RESULT', 'graph_donor_lookup_failed'); return {} end
if safe(function() return game.assets.get_resource(CLONE_GUID, GRAPH_TYPE, 0) end) then
    log('RESULT', 'clone_guid_collision'); return {}
end
local ok_clone, clone = pcall(function()
    return game.assets.register_resource(donor.data, GRAPH_TYPE, CLONE_GUID, 0)
end)
if not ok_clone or not clone then log('RESULT', 'clone_registration_failed|' .. tostring(clone)); return {} end
local clone_readback = safe(function() return game.assets.get_resource(CLONE_GUID, GRAPH_TYPE, 0) end)
if not clone_readback or not clone_readback.data then log('RESULT', 'clone_readback_failed'); return {} end
log('CLONE', 'guid=' .. tostring(clone_readback.guid) .. '|nodes=' .. tostring(#(clone_readback.data.nodeDefinitions or {})))

local owner = safe(function() return game.assets.get_resource(OWNER_GUID, OWNER_TYPE, 0) end)
if not owner or not owner.data then log('RESULT', 'owner_lookup_failed'); return {} end
local target, matches = nil, 0
for _, npc in pairs(owner.data.npcs or {}) do
    if tostring(npc.debugName) == OWNER_NAME then target = npc; matches = matches + 1 end
end
if not target or matches ~= 1 then log('RESULT', 'owner_entry_cardinality_failed|matches=' .. tostring(matches)); return {} end
local before = tostring(target.physicsSetup and target.physicsSetup.animationGraph2 or '')
if before ~= DONOR_GUID then log('RESULT', 'owner_reference_mismatch|before=' .. before); return {} end
target.physicsSetup.animationGraph2 = CLONE_GUID
local after = tostring(target.physicsSetup.animationGraph2)
log('ATTACHMENT', 'ownerType=' .. OWNER_TYPE .. '|ownerGuid=' .. OWNER_GUID .. '|entry=' .. OWNER_NAME
    .. '|field=physicsSetup.animationGraph2|before=' .. before .. '|after=' .. after)
log('DONOR_PRESERVED', tostring(safe(function() return game.assets.get_resource(DONOR_GUID, GRAPH_TYPE, 0) end) ~= nil))
log('BOUNDARY', 'template=false|entity=false|world=false|save=false')
log('RESULT', after == CLONE_GUID and 'animation_graph_npc_attachment_complete' or 'animation_graph_npc_attachment_failed')
return {}
