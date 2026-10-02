-- Metadata-only inventory: never decodes, creates, assigns, or registers payloads.
local PREFIX = '[CC-ANIMATION-WORLD-METADATA:animation_world_metadata_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local targets = {
    'keen::anim_graph::runtime_graph::AnimationGraphResource2_0',
    'keen::actor::ActorSequenceResource',
    'keen::VoxelWorldResource',
    'keen::VoxelWorldChunkResource',
    'keen::WaterWorldResource',
    'keen::WorldMaterialBlending2Resource',
    'keen::SimpleWorldMaterialResource',
    'keen::WorldKnowledgeObjectResource'
}
log('BEGIN', 'build=1076226|read_only=true|metadata_only=true')
log('API', 'version=' .. tostring(game.api_version) .. '|metadata=' .. type(game.assets and game.assets.get_resource_metadata_by_type))
for _, type_name in ipairs(targets) do
    local ok, rows = pcall(function()
        return game.assets.get_resource_metadata_by_type(type_name, 32) or {}
    end)
    if not ok then
        log('TYPE_ERROR', type_name .. '|error=' .. tostring(rows))
    else
        local count, first_guid, first_part = 0, '', ''
        for _, row in pairs(rows) do
            count = count + 1
            if count == 1 then
                first_guid = tostring(row and row.guid or '')
                first_part = tostring(row and row.part or '')
            end
        end
        log('TYPE', type_name .. '|count=' .. count .. '|first=' .. first_guid .. '|part=' .. first_part)
    end
end
log('RESULT', 'animation_world_metadata_inventory_complete')
log('END', 'build=1076226')
return {}
