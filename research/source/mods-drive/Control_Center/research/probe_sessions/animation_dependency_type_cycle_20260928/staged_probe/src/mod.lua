-- Resolve known dependency GUIDs to descriptor types without decoding payloads.
local PREFIX = '[CC-ANIMATION-DEPENDENCY-TYPES:animation_dependency_type_probe_1076226] '
local GUIDS = {
  'eb4405cd-e28f-49b8-81f0-350f1c4bc42f', '8fea0ba1-5bfc-4c6e-87f5-3363a80a9b97',
  '44d1502d-7971-4850-ba50-1e2a86854232', 'e0c546cd-5137-4ab1-bc35-f25892f7a6d7',
  '0aa9f281-0454-4e19-9836-c6ca09938279', '2926da1a-4128-496a-8e7d-db307ab1471e',
  'a5b7e392-6a73-4b62-bde8-c3caae388e66', '274d0053-f8de-420f-a0a9-73f5d1e674d0',
  '48eade49-2dde-47bb-9d0b-6eca9117ad94', '2b1ceab2-09ba-41e0-864c-c98d949cf852',
  'c33410a9-fa05-4860-849e-c2ce26f99004', '6bec9dff-fcf1-4a8b-9ade-77dd5ccd1344',
  'ac790199-c617-44f8-84b9-32f92c98cdf4', '8e8fd516-9a8b-4e1c-939f-76051e6b595f',
  'c49fb5b8-b009-4f7d-8926-6830fc78ee41', 'ccebd609-6c60-4b85-9cac-c218804c8caa',
  '560ef428-7854-4249-9466-7188a4b4ac7a', 'f46c0d0d-2c8c-4189-8893-edb74832529c',
  'a00575be-e6cf-4967-bb85-545eb7f07217', '0e71fc1f-fc1c-4cc3-ba0a-c677f6087c8b',
  '90558ee5-3e3f-45f5-a0a9-c278d66fd985', '5e4627ba-a4b4-4f6a-9550-997cd1e1741f',
  '0b628365-f600-4b0a-b872-8d0183279818', '75f2a071-14c7-4f5e-a4ec-42e6620d2166',
  'c1d4322a-936f-46ae-9219-17ead43f4563', 'aa54ca97-9abc-4540-9378-441d834fb177',
  'a9cfc778-451d-49f7-be49-cff91dce2af3', 'f8265a18-c7af-4968-8940-cdbe6862685c',
  '51a6c90c-8a85-4095-9816-4d59f97a0006', '6b3e39bc-26fc-48fa-ab44-2bdaf552c74e',
  '4069168e-de1f-4d66-88dd-2a9a8a06b865', '0d94977f-ed2b-401e-ad3d-9bae0089e2a4'
}
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end

log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|read_only=true|guids=' .. tostring(#GUIDS))
if tostring(game.api_version) ~= '1.3' or type(game.assets.get_resource_metadata_by_guid) ~= 'function' then
  log('RESULT', 'required_api_unavailable')
  return {}
end

local resolved, unresolved, matches = 0, 0, 0
for _, guid in ipairs(GUIDS) do
  local ok, rows = pcall(function() return game.assets.get_resource_metadata_by_guid(guid) or {} end)
  if not ok then
    unresolved = unresolved + 1
    log('ERROR', guid .. '|lookup_failed=' .. tostring(rows))
  elseif #rows == 0 then
    unresolved = unresolved + 1
    log('UNRESOLVED', guid)
  else
    resolved = resolved + 1
    for _, row in ipairs(rows) do
      matches = matches + 1
      log('RESOLVED', guid .. '|type=' .. tostring(row.type) .. '|part=' .. tostring(row.part))
    end
  end
end
log('SUMMARY', 'requested=' .. tostring(#GUIDS) .. '|resolved=' .. tostring(resolved) .. '|unresolved=' .. tostring(unresolved) .. '|matches=' .. tostring(matches))
log('ATTACHMENT', 'animation=false|entity=false|world=false|save=false')
log('RESULT', unresolved == 0 and 'dependency_type_resolution_complete' or 'dependency_type_resolution_partial')
return {}
