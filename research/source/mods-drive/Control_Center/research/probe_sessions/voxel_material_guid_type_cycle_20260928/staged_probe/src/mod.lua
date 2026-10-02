-- Resolve a bounded sample of VoxelWorld material GUIDs without payload decoding.
local PREFIX = '[CC-VOXEL-MATERIAL-TYPE:voxel_material_guid_type_probe_1076226] '
local GUIDS = {
  'd0122ac2-e754-6d46-a4f6-8ef1e3844253',
  '32f356d7-1d8b-8f48-b78a-78a7c6270ae9',
  'a611910b-b99e-d243-a0a6-54dcaaeb7239',
  'f9a76471-1ceb-2642-8765-8c11c492a343',
  '1b0f8c72-5954-4a48-911d-f81ca3b467c6',
  'fa03ae6b-2577-0345-b3c1-052b275eac27',
  '2484fd4e-1db1-cc4d-8e73-1fc1c955091c',
  '1ae68c4f-820c-1c48-9bdd-af76e8be74b6',
  '346e9207-169c-5649-9ff0-168327e050aa',
  'b2b55117-a985-3a46-89f8-047ffe257fcc',
  'ec2b40c4-9a63-8e4c-8cdd-29c531c20412',
  '1da160f1-8db4-b744-b8c4-c4ef633f1515',
}

local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end

log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|read_only=true|metadata_only=true|sample=' .. tostring(#GUIDS))
if tostring(game.api_version) ~= '1.3' or type(game.assets.get_resource_metadata_by_guid) ~= 'function' then
  log('RESULT', 'api_mismatch')
  return {}
end

local resolved = 0
local matches = 0
for _, guid in ipairs(GUIDS) do
  local ok, rows = pcall(function() return game.assets.get_resource_metadata_by_guid(guid) or {} end)
  local count = ok and #rows or 0
  if count > 0 then resolved = resolved + 1 end
  matches = matches + count
  log('GUID', guid .. '|ok=' .. tostring(ok) .. '|count=' .. tostring(count))
  if ok then
    for _, row in ipairs(rows) do
      log('MATCH', guid .. '|type=' .. tostring(row.type) .. '|part=' .. tostring(row.part))
    end
  end
end
log('BOUNDARY', 'payload=false|created=false|registered=false|mutated=false|world=false|save=false')
log('RESULT', 'voxel_material_metadata_complete|sample=' .. tostring(#GUIDS) .. '|resolved=' .. tostring(resolved) .. '|matches=' .. tostring(matches))
log('END', 'build=1076226')
return {}
