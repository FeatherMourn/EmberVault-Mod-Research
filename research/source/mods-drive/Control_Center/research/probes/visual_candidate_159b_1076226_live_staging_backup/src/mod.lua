-- Generated visual substitution probe; research-only and read-only.
local RESOURCE_TYPE = "keen::RenderModel"
local DEPENDENCIES = {"159b5f47-aa61-4db9-8e64-06db850de6f6", "7e2dfdb4-4066-4a25-81fd-7df722c97307", "c936cd1a-5a70-40ac-b897-7be0d2ccd328", "ae2dfe34-3510-45b6-b1d8-a6751c440c4c", "17e7e9bb-14d6-4dbe-9a49-2bb10d655b7b"}
local function log(kind, value)
    print("[CC-VISUAL-PROBE:visual_candidate_159b_1076226] " .. kind .. "|" .. tostring(value or ""))
end
local resources = game.assets.get_resources_by_type(RESOURCE_TYPE) or {}
local found = {}
for _, resource in pairs(resources) do
    local guid = tostring(resource and resource.guid or "")
    if guid ~= "" then found[guid] = true end
end
for _, dependency in ipairs(DEPENDENCIES) do
    log("DEPENDENCY", dependency .. "|" .. tostring(found[dependency] == true))
end
log("GRAPH_SCAN", RESOURCE_TYPE .. "|count=" .. tostring(#resources))
log("ACTION", "read_only_no_visual_mutation")
return {}
