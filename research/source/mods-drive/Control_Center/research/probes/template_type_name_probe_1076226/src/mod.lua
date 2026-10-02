-- Read-only type-name probe.
local function log(kind, value)
    print("[CC-TEMPLATE-TYPE:template_type_name_probe_1076226] " .. kind .. "|" .. tostring(value or ""))
end
log("BEGIN", "TemplateResource")
local ok, resources = pcall(function()
    return game.assets.get_resources_by_type("TemplateResource") or {}
end)
log("CALL", tostring(ok) .. "|" .. tostring(resources))
if ok and resources then
    local count = 0
    for _, resource in pairs(resources) do count = count + 1 end
    log("SCAN", tostring(count))
end
log("END", "read_only")
return {}
