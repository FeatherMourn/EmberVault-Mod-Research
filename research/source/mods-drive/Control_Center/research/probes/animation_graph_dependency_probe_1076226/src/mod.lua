-- Bounded dependency traversal of one known graph. No writes or attachments.
local PREFIX = '[CC-ANIMATION-GRAPH-DEPS:animation_graph_dependency_probe_1076226] '
local TYPE = 'keen::anim_graph::runtime_graph::AnimationGraphResource2_0'
local GUID = '0022fed6-0380-4125-be31-ba8b5fdcbfcd'
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function safe(callback) local ok, value = pcall(callback); if ok then return value end; return nil end
local dependencies, type_counts = {}, {}
local function dependency(role, value)
    local text = tostring(value or '')
    if text ~= '' and text ~= '00000000-0000-0000-0000-000000000000' then
        dependencies[text] = dependencies[text] or {}
        dependencies[text][role] = true
    end
end

log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|read_only=true|max_nodes=128')
local resource = safe(function() return game.assets.get_resource(GUID, TYPE, 0) end)
if not resource then log('RESULT', 'resource_lookup_failed'); return {} end
local data = safe(function() return resource.data end)
if not data then log('RESULT', 'payload_read_failed'); return {} end
dependency('hierarchy', safe(function() return data.hierarchy end))
dependency('clothColliderReference', safe(function() return data.clothColliderReference end))
local traversed = 0
for index, node in pairs(data.nodeDefinitions or {}) do
    traversed = traversed + 1
    if traversed > 128 then log('BOUNDARY', 'node_limit_reached'); break end
    local node_type = tostring(safe(function() return node.type end) or 'unknown')
    type_counts[node_type] = (type_counts[node_type] or 0) + 1
    local value = safe(function() return node.value end)
    if value then
        dependency('animation', safe(function() return value.animation end))
        dependency('additiveReferenceAnimation', safe(function() return value.additiveReferenceAnimation end))
        dependency('rootMotionAnimation', safe(function() return value.rootMotionAnimation end))
        local items = safe(function() return value.items end)
        if items then
            for _, item in pairs(items) do
                dependency('blendSpaceAnimation', safe(function() return item.animation end))
            end
        end
    end
end
local unique_types = 0
for node_type, count in pairs(type_counts) do
    unique_types = unique_types + 1
    log('NODE_TYPE', node_type .. '|count=' .. tostring(count))
end
local dependency_count = 0
for guid, roles in pairs(dependencies) do
    dependency_count = dependency_count + 1
    local names = {}
    for role, _ in pairs(roles) do names[#names + 1] = role end
    table.sort(names)
    log('DEPENDENCY', guid .. '|roles=' .. table.concat(names, ','))
end
log('SUMMARY', 'nodes=' .. tostring(traversed) .. '|types=' .. tostring(unique_types) .. '|dependencies=' .. tostring(dependency_count))
log('ATTACHMENT', 'animation=false|entity=false|world=false|save=false')
log('RESULT', 'animation_graph_dependency_traversal_complete')
return {}
