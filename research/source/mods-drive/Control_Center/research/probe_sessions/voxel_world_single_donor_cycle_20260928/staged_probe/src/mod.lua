-- One-resource VoxelWorld payload boundary probe.
-- No mutation, creation, registration, attachment, world access, or save access.
local PREFIX = '[CC-VOXEL-WORLD-DONOR:voxel_world_single_donor_probe_1076226] '
local TYPE = 'keen::VoxelWorldResource'
local GUID = '022bd475-089a-43b8-b49a-2bcf2f0cd84f'

local function log(kind, value)
    print(PREFIX .. kind .. '|' .. tostring(value or ''))
end

local function read(label, callback)
    local ok, value = pcall(callback)
    log('FIELD', label .. '|ok=' .. tostring(ok) .. '|value=' .. tostring(value))
    return ok, value
end

log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|read_only=true|bounded=true')
if tostring(game.api_version) ~= '1.3' then
    log('RESULT', 'api_mismatch')
    return {}
end

log('PHASE', 'before_resource_lookup')
local ok, resource = pcall(function()
    return game.assets.get_resource(GUID, TYPE, 0)
end)
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

read('type', function() return data.type end)
read('size_x', function() return data.size.x end)
read('size_y', function() return data.size.y end)
read('size_z', function() return data.size.z end)
read('origin_x', function() return data.origin.x end)
read('origin_y', function() return data.origin.y end)
read('origin_z', function() return data.origin.z end)
read('material_count', function() return #data.materialGuids end)
read('default_terrain_material', function() return data.defaultTerrainMaterial end)
read('voxel_level_count', function() return #data.voxelLevels end)
read('level_0_tile_size_x', function() return data.voxelLevels[1].tileSize.x end)
read('level_0_tile_size_y', function() return data.voxelLevels[1].tileSize.y end)
read('level_0_tile_count_x', function() return data.voxelLevels[1].tileCount.x end)
read('level_0_tile_count_y', function() return data.voxelLevels[1].tileCount.y end)
read('level_0_tiles_count', function() return #data.voxelLevels[1].tiles end)
read('cpu_displacement_size', function() return data.cpuDisplacement.size end)
read('voxel_hashes_size', function() return data.voxelHashes.size end)

log('BOUNDARY', 'created=false|registered=false|mutated=false|attached=false|world=false|save=false')
log('RESULT', 'single_voxel_world_payload_read_complete')
log('END', 'build=1076226')
return {}
