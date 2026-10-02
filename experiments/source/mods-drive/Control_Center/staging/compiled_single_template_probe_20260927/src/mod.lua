-- Generated single-resource probe; research-only and read-only.
local TYPE_NAME = "keen::TemplateResource"
local WANTED_GUID = "9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5"
local function log(kind, value)
    print("[CC-SINGLE-RESOURCE:single_template_probe_20260927] " .. kind .. "|" .. tostring(value or ""))
end
local ok, result = pcall(function()
    return game.assets.get_resources_by_type(TYPE_NAME) or {}
end)
if not ok then
    log("TYPE_ERROR", tostring(result))
    return {}
end
local resources = result or {}
local found = false
for _, resource in pairs(resources) do
    if resource and tostring(resource.guid) == WANTED_GUID then found = true; break end
end
log("RESULT", TYPE_NAME .. "|" .. WANTED_GUID .. "|" .. tostring(found))
log("COUNT", #resources)
log("ACTION", "read_only_single_lookup")
return {}
