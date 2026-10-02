-- Generated bounded resource metadata probe; read-only.
local TYPE_NAME = "keen::ItemInfo"
local WANTED_GUID = "01474f79-6b5a-4bcd-999d-7e9339fda91c"
local function log(kind, value)
    print("[CC-RESOURCE-METADATA:iteminfo_metadata_single_20260928] " .. tostring(kind) .. "|" .. tostring(value or ""))
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
