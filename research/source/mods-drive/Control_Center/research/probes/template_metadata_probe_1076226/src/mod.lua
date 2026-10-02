-- Requires the rebuilt EML metadata-only lookup; read-only.
local GUID = "9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5"
local TYPE = "keen::TemplateResource"
local function log(kind, value)
    print("[CC-TEMPLATE-METADATA:template_metadata_probe_1076226] " .. kind .. "|" .. tostring(value or ""))
end
log("BEGIN", GUID)
local ok, metadata = pcall(function()
    return game.assets.get_resource_metadata(GUID, TYPE, 0)
end)
log("CALL", tostring(ok))
if not ok then log("ERROR", metadata); return {} end
if not metadata then log("RESULT", "missing"); return {} end
log("RESULT", "found")
log("TYPE", metadata.type)
log("PART", metadata.part)
log("ACTION", "metadata_only_no_decode")
return {}
