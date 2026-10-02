-- Read-only exact GUID lookup; no enumeration or mutation.
local GUID = "9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5"
local TYPE = "keen::TemplateResource"
local function log(kind, value)
    print("[CC-TEMPLATE-GUID:template_guid_lookup_probe_1076226] " .. kind .. "|" .. tostring(value or ""))
end
log("BEGIN", GUID)
local ok, resource = pcall(function()
    return game.assets.get_resource(GUID, TYPE, 0)
end)
log("CALL", tostring(ok))
if not ok then log("ERROR", resource); return {} end
if not resource then log("RESULT", "missing"); return {} end
log("RESULT", "found")
log("TYPE", resource.type)
log("PART", resource.part_index)
log("DATA", tostring(resource.data ~= nil))
return {}
