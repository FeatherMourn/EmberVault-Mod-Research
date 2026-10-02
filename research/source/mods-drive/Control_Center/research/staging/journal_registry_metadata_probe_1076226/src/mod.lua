-- Generated bounded resource metadata probe; read-only.
local TYPE_NAME = "keen::JournalRegistryResource"
local WANTED_GUID = "33701b26-ec1d-423f-8e06-49f023b91b7f"
local function log(kind, value)
    print("[CC-RESOURCE-METADATA:journal_registry_metadata_probe_1076226] " .. tostring(kind) .. "|" .. tostring(value or ""))
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
