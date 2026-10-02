-- Generated resource metadata probe; research-only and read-only.
local TYPE_NAME = "keen::ItemInfo"
local WANTED_GUID = "01474f79-6b5a-4bcd-999d-7e9339fda91c"
local function log(kind, value)
    print("[CC-RESOURCE-METADATA:iteminfo_metadata_by_type_20260928] " .. tostring(kind) .. "|" .. tostring(value or ""))
end
-- Record the live API surface before attempting the call. This makes a
-- loader/API mismatch immediately distinguishable from a bad resource type.
log("API", "assets=" .. type(game.assets) .. "|metadata=" .. type(game.assets and game.assets.get_resource_metadata_by_type) .. "|resources=" .. type(game.assets and game.assets.get_resources_by_type))
local ok, result = pcall(function()
    return game.assets.get_resource_metadata_by_type(TYPE_NAME) or {}
end)
if not ok then log("TYPE_ERROR", tostring(result)); return {} end
local found = false
local count = 0
for _, row in pairs(result or {}) do
    count = count + 1
    if row and tostring(row.guid) == WANTED_GUID then
        found = true
        log("MATCH", tostring(row.guid) .. "|part=" .. tostring(row.part))
    end
end
log("COUNT", count)
log("RESULT", tostring(found))
log("ACTION", "read_only_metadata_identity")
return {}
