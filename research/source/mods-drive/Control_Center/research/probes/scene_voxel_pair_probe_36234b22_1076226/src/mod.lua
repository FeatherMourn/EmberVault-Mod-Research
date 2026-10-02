-- Read one small SceneResource and its same-GUID solid/fog VoxelWorld pair.
-- No creation, registration, mutation, attachment, binary content, world, or save access.
local PREFIX = '[CC-SCENE-VOXEL-PAIR:scene_voxel_pair_probe_36234b22_1076226] '
local GUID = '36234b22-85f2-4001-ac56-002b379d0d88'
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function read(label, callback)
  local ok, value = pcall(callback)
  log('FIELD', label .. '|ok=' .. tostring(ok) .. '|value=' .. tostring(value))
  return ok, value
end
local function lookup(label, type_name, part)
  log('PHASE', 'before_lookup|' .. label)
  local ok, resource = pcall(function() return game.assets.get_resource(GUID, type_name, part) end)
  log('LOOKUP', label .. '|ok=' .. tostring(ok) .. '|found=' .. tostring(resource ~= nil) .. '|part=' .. tostring(part))
  if not ok or not resource then return nil end
  read(label .. '_guid', function() return resource.guid end)
  local data_ok, data = pcall(function() return resource.data end)
  log('PAYLOAD', label .. '|ok=' .. tostring(data_ok) .. '|type=' .. type(data))
  if not data_ok then return nil end
  return data
end
local function tile_count(data)
  local total = 0
  for index = 1, #data.voxelLevels do total = total + #data.voxelLevels[index].tiles end
  return total
end

log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|read_only=true|paired=true')
if tostring(game.api_version) ~= '1.3' then log('RESULT', 'api_mismatch') return {} end

local scene = lookup('scene', 'keen::SceneResource', 0)
if not scene then log('RESULT', 'scene_read_failed') return {} end
read('scene_nodes', function() return #scene.nodes end)
read('scene_models', function() return #scene.models end)
read('scene_lights', function() return #scene.lights end)
read('scene_cameras', function() return #scene.cameras end)
read('scene_vfxs', function() return #scene.vfxs end)
read('scene_sounds', function() return #scene.sounds end)
read('scene_entity_chunks_x', function() return scene.entityChunkCount.x end)
read('scene_entity_chunks_y', function() return scene.entityChunkCount.y end)
read('scene_ibl_intensity', function() return scene.iblIntensity end)

local solid = lookup('solid', 'keen::VoxelWorldResource', 0)
if not solid then log('RESULT', 'solid_read_failed') return {} end
read('solid_type', function() return solid.type end)
read('solid_size_x', function() return solid.size.x end)
read('solid_size_y', function() return solid.size.y end)
read('solid_size_z', function() return solid.size.z end)
read('solid_material_count', function() return #solid.materialGuids end)
read('solid_level_count', function() return #solid.voxelLevels end)
read('solid_tile_count', function() return tile_count(solid) end)
read('solid_default_material', function() return solid.defaultTerrainMaterial end)

local fog = lookup('fog', 'keen::VoxelWorldResource', 1)
if not fog then log('RESULT', 'fog_read_failed') return {} end
read('fog_type', function() return fog.type end)
read('fog_size_x', function() return fog.size.x end)
read('fog_size_y', function() return fog.size.y end)
read('fog_size_z', function() return fog.size.z end)
read('fog_material_count', function() return #fog.materialGuids end)
read('fog_level_count', function() return #fog.voxelLevels end)
read('fog_tile_count', function() return tile_count(fog) end)
read('fog_default_material', function() return fog.defaultTerrainMaterial end)

log('RELATION', 'shared_guid=true|scene_part=0|solid_part=0|fog_part=1')
log('BOUNDARY', 'content=false|created=false|registered=false|mutated=false|attached=false|world=false|save=false')
log('RESULT', 'scene_voxel_pair_read_complete')
log('END', 'build=1076226')
return {}
