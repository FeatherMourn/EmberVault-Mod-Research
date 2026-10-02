-- Generated resource metadata probe; research-only and read-only.
local TYPE_NAME = "keen::TemplateResource"
local WANTED_GUID = "9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5"
local function log(kind, value)
    print("[CC-RESOURCE-METADATA:template_resource_metadata_1076226] " .. tostring(kind) .. "|" .. tostring(value or ""))
end
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
