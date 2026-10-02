-- Generated bounded resource metadata probe; read-only.
local TYPE_NAME = "keen::VoxelBlueprintItemRegistryResource"
local WANTED_GUID = "3064d35d-7342-40ca-bdc9-aad58f83bf45"
local function log(kind, value)
    print("[CC-RESOURCE-METADATA:voxel_blueprint_registry_metadata_probe_20260929] " .. tostring(kind) .. "|" .. tostring(value or ""))
end
log("API", "metadata=" .. type(game.assets and game.assets.get_resource_metadata))
log("BEFORE_CALL", TYPE_NAME .. "|" .. WANTED_GUID)
local ok, result = pcall(function()
    return game.assets.get_resource_metadata(WANTED_GUID, TYPE_NAME, 0)
end)
log("AFTER_CALL", "ok=" .. tostring(ok) .. "|result=" .. tostring(result))
if ok and result then
    log("IDENTITY", "guid=" .. tostring(result.guid) .. "|type=" .. tostring(result.type) .. "|part=" .. tostring(result.part))
end
return {}
