-- Bounded FogVoxelMappingResource payload read. No voxel/chunk content access.
local PREFIX = '[CC-FOG-VOXEL-MAPPING:fog_voxel_mapping_single_donor_probe_36234b22_1076226] '
local GUID = '36234b22-85f2-4001-ac56-002b379d0d88'
local TYPE = 'keen::FogVoxelMappingResource'
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function read(label, callback)
  local ok, value = pcall(callback)
  log('FIELD', label .. '|ok=' .. tostring(ok) .. '|value=' .. tostring(value))
  return ok, value
end
log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|read_only=true|bounded=true')
if tostring(game.api_version) ~= '1.3' then log('RESULT', 'api_mismatch') return {} end
local ok, resource = pcall(function() return game.assets.get_resource(GUID, TYPE, 0) end)
log('LOOKUP', 'ok=' .. tostring(ok) .. '|found=' .. tostring(resource ~= nil))
if not ok or not resource then log('RESULT', 'resource_lookup_failed') return {} end
read('guid', function() return resource.guid end)
local data_ok, data = pcall(function() return resource.data end)
log('PAYLOAD', 'ok=' .. tostring(data_ok) .. '|type=' .. type(data))
if not data_ok or not data then log('RESULT', 'payload_read_failed') return {} end
read('mapping_count', function() return #data.mapping end)
read('first_type', function() return data.mapping[1].type end)
read('first_level', function() return data.mapping[1].level end)
read('first_min_x', function() return data.mapping[1].boundingBox.min.x end)
read('first_max_z', function() return data.mapping[1].boundingBox.max.z end)
read('last_type', function() return data.mapping[#data.mapping].type end)
read('last_level', function() return data.mapping[#data.mapping].level end)
log('BOUNDARY', 'voxel_content=false|chunk_content=false|created=false|registered=false|mutated=false|attached=false|world=false|save=false')
log('RESULT', 'fog_voxel_mapping_payload_read_complete')
log('END', 'build=1076226')
return {}
