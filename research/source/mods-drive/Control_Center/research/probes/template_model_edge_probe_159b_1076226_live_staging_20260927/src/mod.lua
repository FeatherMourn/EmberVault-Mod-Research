-- Minimal clone-only TemplateResource model-edge probe; research-only.
local TEMPLATE_GUID = "9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5"
local REPLACEMENT_MODEL = "159b5f47-aa61-4db9-8e64-06db850de6f6"
local function log(kind, value)
    print("[CC-TEMPLATE-EDGE:template_model_edge_probe_159b_1076226] " .. kind .. "|" .. tostring(value or ""))
end
local ok, resources = pcall(function()
    return game.assets.get_resources_by_type("keen::TemplateResource") or {}
end)
if not ok then log("TYPE_ERROR", resources); return {} end
local found
local count = 0
for _, resource in pairs(resources) do
    count = count + 1
    if resource and tostring(resource.guid or "") == TEMPLATE_GUID then found = resource; break end
end
log("GRAPH_SCAN", "keen::TemplateResource|count=" .. tostring(count))
if not found or not found.data then log("TEMPLATE", "missing"); return {} end
log("TEMPLATE", "found")
local ok_clone, clone = pcall(function()
    return game.assets.register_resource(found.data, "keen::TemplateResource")
end)
if not ok_clone or not clone or not clone.data then log("CLONE_ERROR", clone); return {} end
local components = clone.data.components
local changed = false
if components then
    for _, component in pairs(components) do
        local value = component and component["$value"]
        if value and tostring(value.model or "") ~= "" then
            local before = value.model
            local ok_assign, err = pcall(function() value.model = REPLACEMENT_MODEL end)
            log("ASSIGN", tostring(ok_assign) .. "|" .. tostring(err or ""))
            log("BEFORE", before)
            log("AFTER", value.model)
            changed = ok_assign
            break
        end
    end
end
log("ACTION", changed and "clone_only_no_registry_mutation" or "no_model_edge_found")
return {}
