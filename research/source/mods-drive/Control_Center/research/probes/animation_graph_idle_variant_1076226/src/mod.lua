-- Reroute only the cloned Hunter graph's idle state to an existing same-graph pose.
local GRAPH_TYPE = 'keen::anim_graph::runtime_graph::AnimationGraphResource2_0'
local DONOR_GUID = '0022fed6-0380-4125-be31-ba8b5fdcbfcd'
local CLONE_GUID = 'e24552b9-ccbc-4d4a-a922-939381658b37'
local OWNER_TYPE, OWNER_GUID = 'keen::NpcCollection', '377f61dc-c7b8-4e4f-830f-7d2c3e8b7fd8'
local OWNER_NAME = 'NPC_Workshop_Hunter01'
local IDLE_STATE_ID, IDLE_POSE, VARIANT_POSE = 2226547610, 2585692075, 3890759935
local PREFIX = '[CC-ANIMATION-IDLE-VARIANT:animation_graph_idle_variant_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function safe(callback) local ok, value = pcall(callback); if ok then return value end; return nil end

log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|edit=idle_to_idle_Var_02')
local donor = safe(function() return game.assets.get_resource(DONOR_GUID, GRAPH_TYPE, 0) end)
if not donor or not donor.data then log('RESULT', 'donor_lookup_failed'); return {} end
if safe(function() return game.assets.get_resource(CLONE_GUID, GRAPH_TYPE, 0) end) then log('RESULT', 'clone_guid_collision'); return {} end
local ok_clone, clone = pcall(function() return game.assets.register_resource(donor.data, GRAPH_TYPE, CLONE_GUID, 0) end)
if not ok_clone or not clone or not clone.data then log('RESULT', 'clone_registration_failed|' .. tostring(clone)); return {} end

local edited, before, after = 0, nil, nil
for _, node in pairs(clone.data.nodeDefinitions or {}) do
    local value = safe(function() return node.value end)
    if value and tonumber(safe(function() return value.id.value end)) == IDLE_STATE_ID then
        before = tonumber(safe(function() return value.poseResult.value end))
        if before ~= IDLE_POSE then log('RESULT', 'idle_pose_mismatch|before=' .. tostring(before)); return {} end
        value.poseResult.value = VARIANT_POSE
        after = tonumber(value.poseResult.value)
        edited = edited + 1
    end
end
if edited ~= 1 or after ~= VARIANT_POSE then log('RESULT', 'edit_cardinality_failed|edited=' .. edited .. '|after=' .. tostring(after)); return {} end
log('GRAPH_EDIT', 'clone=' .. CLONE_GUID .. '|state=idle|stateId=' .. IDLE_STATE_ID .. '|beforePose=' .. before .. '|afterPose=' .. after .. '|targetState=idle_Var_02')

local owner = safe(function() return game.assets.get_resource(OWNER_GUID, OWNER_TYPE, 0) end)
if not owner or not owner.data then log('RESULT', 'owner_lookup_failed'); return {} end
local target, matches = nil, 0
for _, npc in pairs(owner.data.npcs or {}) do if tostring(npc.debugName) == OWNER_NAME then target=npc; matches=matches+1 end end
if not target or matches ~= 1 then log('RESULT', 'owner_cardinality_failed|matches=' .. matches); return {} end
local owner_before = tostring(target.uiRendering and target.uiRendering.animationGraph2 or '')
if owner_before ~= DONOR_GUID then log('RESULT', 'owner_reference_mismatch|before=' .. owner_before); return {} end
target.uiRendering.animationGraph2 = CLONE_GUID
log('ATTACHMENT', 'owner=' .. OWNER_NAME .. '|field=uiRendering.animationGraph2|before=' .. owner_before .. '|after=' .. tostring(target.uiRendering.animationGraph2))
log('DONOR_PRESERVED', tostring(safe(function() return game.assets.get_resource(DONOR_GUID, GRAPH_TYPE, 0) end) ~= nil))
log('BOUNDARY', 'template=false|entity=false|world=false|save=false|animationPayload=false')
log('RESULT', 'animation_graph_idle_variant_attached')
return {}
