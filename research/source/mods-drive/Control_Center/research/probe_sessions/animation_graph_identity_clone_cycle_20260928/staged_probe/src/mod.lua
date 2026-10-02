-- Donor-preserving animation graph identity clone. No entity/world/save attachment.
local TYPE = 'keen::anim_graph::runtime_graph::AnimationGraphResource2_0'
local DONOR_GUID = '0022fed6-0380-4125-be31-ba8b5fdcbfcd'
local CLONE_GUID = '7d3109de-80a7-44ad-a549-680460153d46'
local PREFIX = '[CC-ANIMATION-GRAPH-CLONE:animation_graph_identity_clone_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function safe(callback) local ok, value = pcall(callback); if ok then return value end; return nil end

local function signature(data)
    local node_count, type_counts, dependencies = 0, {}, {}
    local function dependency(value)
        local text = tostring(value or '')
        if text ~= '' and text ~= '00000000-0000-0000-0000-000000000000' then dependencies[text] = true end
    end
    dependency(safe(function() return data.hierarchy end))
    dependency(safe(function() return data.clothColliderReference end))
    for _, node in pairs(data.nodeDefinitions or {}) do
        node_count = node_count + 1
        local node_type = tostring(safe(function() return node.type end) or 'unknown')
        type_counts[node_type] = (type_counts[node_type] or 0) + 1
        local value = safe(function() return node.value end)
        if value then
            dependency(safe(function() return value.animation end))
            dependency(safe(function() return value.additiveReferenceAnimation end))
            dependency(safe(function() return value.rootMotionAnimation end))
            for _, item in pairs(safe(function() return value.items end) or {}) do
                dependency(safe(function() return item.animation end))
            end
        end
    end
    local types, deps = {}, {}
    for name, count in pairs(type_counts) do types[#types + 1] = name .. '=' .. tostring(count) end
    for guid in pairs(dependencies) do deps[#deps + 1] = guid end
    table.sort(types); table.sort(deps)
    return node_count, table.concat(types, ','), table.concat(deps, ','), #deps
end

log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|attach=false')
local donor = safe(function() return game.assets.get_resource(DONOR_GUID, TYPE, 0) end)
if not donor or not donor.data then log('RESULT', 'donor_lookup_failed'); return {} end
if safe(function() return game.assets.get_resource(CLONE_GUID, TYPE, 0) end) then
    log('RESULT', 'clone_guid_collision'); return {}
end
local donor_nodes, donor_types, donor_dependencies, donor_dependency_count = signature(donor.data)
log('DONOR', 'guid=' .. DONOR_GUID .. '|nodes=' .. donor_nodes .. '|dependencies=' .. donor_dependency_count)

local ok_helper, helper = pcall(require, 'kfc_content_registry')
if not ok_helper then log('RESULT', 'helper_load_failed|' .. tostring(helper)); return {} end
local clone, clone_error = helper.clone_resource(donor, TYPE, CLONE_GUID, 0)
if not clone then log('RESULT', 'clone_registration_failed|' .. tostring(clone_error)); return {} end
local readback = safe(function() return game.assets.get_resource(CLONE_GUID, TYPE, 0) end)
if not readback or not readback.data then log('RESULT', 'clone_readback_failed'); return {} end
local clone_nodes, clone_types, clone_dependencies, clone_dependency_count = signature(readback.data)
local donor_preserved = safe(function() return game.assets.get_resource(DONOR_GUID, TYPE, 0) end) ~= nil
log('CLONE', 'guid=' .. tostring(readback.guid) .. '|nodes=' .. clone_nodes .. '|dependencies=' .. clone_dependency_count)
log('PARITY', 'nodes=' .. tostring(donor_nodes == clone_nodes)
    .. '|types=' .. tostring(donor_types == clone_types)
    .. '|dependencies=' .. tostring(donor_dependencies == clone_dependencies))
log('DONOR_PRESERVED', tostring(donor_preserved))
log('ATTACHMENT', 'animation=false|entity=false|world=false|save=false')
if donor_nodes == clone_nodes and donor_types == clone_types and donor_dependencies == clone_dependencies and donor_preserved then
    log('RESULT', 'animation_graph_identity_clone_complete')
else
    log('RESULT', 'animation_graph_identity_clone_parity_failed')
end
return {}
