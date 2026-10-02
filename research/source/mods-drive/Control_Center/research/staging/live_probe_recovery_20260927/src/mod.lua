-- Generated visual substitution probe; research-only and read-only.
local RESOURCE_TYPE = "keen::RenderModel"
local DEPENDENCIES = {"visual"}
local function log(kind, value)
    print("[CC-VISUAL-PROBE:visual_candidate_graph_probe_1076226_v2] " .. kind .. "|" .. tostring(value or ""))
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
