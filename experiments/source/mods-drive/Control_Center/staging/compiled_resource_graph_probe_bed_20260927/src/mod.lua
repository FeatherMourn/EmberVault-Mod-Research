-- Generated resource graph probe; research-only and read-only.
local GUIDS = {"4c7f1c3a-b448-4460-ad5e-a79b3859d2c1", "bb6e4131-f978-4707-bd0c-f573d59b1d37"}
local TYPES = {"keen::TemplateResource", "keen::RenderModel", "keen::FbUiBundle"}
local function log(kind, value)
    print("[CC-RESOURCE-GRAPH:resource_graph_probe_bed_20260927] " .. kind .. "|" .. tostring(value or ""))
end
for _, type_name in ipairs(TYPES) do
    local ok, result = pcall(function() return game.assets.get_resources_by_type(type_name) end)
      if not ok then
          log("TYPE_ERROR", type_name .. "|" .. tostring(result))
      else
          local resources = result or {}
          for _, resource in pairs(resources) do
              local guid = tostring(resource and resource.guid or "")
              for _, wanted in ipairs(GUIDS) do
                  if guid == wanted then
                      log("MATCH", wanted .. "|" .. type_name)
                  end
            end
        end
          log("TYPE_SCAN", type_name .. "|count=" .. tostring(#resources))
    end
end
log("ACTION", "read_only_resource_graph")
return {}
