-- Read-only runtime inventory. No assignments, resource creation, or registry writes.
local PREFIX = '[CC-ANIMATION-WORLD-SCHEMA:animation_world_schema_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local targets = {
    'keen::AnimationGraphResource2_0',
    'keen::ds::AnimationGraphResource2_0',
    'keen::actor::ActorSequenceResource',
    'keen::VoxelWorldResource',
    'keen::VoxelWorldChunkResource',
    'keen::WaterWorldResource',
    'keen::WorldMaterialBlending2Resource',
    'keen::SimpleWorldMaterialResource',
    'keen::WorldKnowledgeObjectResource'
}
log('BEGIN', 'build=1076226|read_only=true')
for _, type_name in ipairs(targets) do
    local ok, resources = pcall(function()
        return game.assets.get_resources_by_type(type_name) or {}
    end)
    if not ok then
        log('TYPE', type_name .. '|call_error=' .. tostring(resources))
    else
        local count = 0
        local first_guid = ''
        for key, resource in pairs(resources) do
            count = count + 1
            if count == 1 then first_guid = tostring(resource and resource.guid or key) end
        end
        log('TYPE', type_name .. '|count=' .. count .. '|first=' .. first_guid)
    end
end
log('RESULT', 'animation_world_schema_inventory_runtime_verified')
log('END', 'build=1076226')
return {}
