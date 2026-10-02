-- Map registered same-GUID scene/chunk families and part ranges only.
local PREFIX = '[CC-SCENE-FAMILY-METADATA:scene_resource_family_metadata_probe_36234b22_1076226] '
local GUID = '36234b22-85f2-4001-ac56-002b379d0d88'
local TYPES = {
  'keen::SceneResource',
  'keen::VoxelWorldResource',
  'keen::VoxelWorldChunkResource',
  'keen::VoxelWorldFog3Resource',
  'keen::WaterWorldResource',
  'keen::WaterChunkResource',
  'keen::SceneEntityChunkResource',
  'keen::RenderModelChunkGridResource',
  'keen::RenderModelChunkModelResource',
  'keen::FogVoxelMappingResource',
}
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|read_only=true|metadata_only=true|guid=' .. GUID)
if tostring(game.api_version) ~= '1.3' or type(game.assets.get_resource_metadata_by_guid) ~= 'function' then log('RESULT', 'api_mismatch') return {} end
for _, type_name in ipairs(TYPES) do
  local ok, rows = pcall(function() return game.assets.get_resource_metadata_by_guid(GUID) or {} end)
  local matching, parts = 0, {}
  if ok then
    for _, row in ipairs(rows) do
      if tostring(row.type) == type_name then matching = matching + 1; parts[#parts + 1] = tostring(row.part) end
    end
  end
  log('TYPE', type_name .. '|ok=' .. tostring(ok) .. '|count=' .. tostring(matching) .. '|parts=' .. table.concat(parts, ','))
end
log('BOUNDARY', 'payload=false|created=false|registered=false|mutated=false|attached=false|world=false|save=false')
log('RESULT', 'scene_resource_family_metadata_complete')
log('END', 'build=1076226')
return {}
