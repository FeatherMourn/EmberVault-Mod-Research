-- Control Center 2: OBSERVE ONLY, manual install on a disposable test setup.
-- Do not run alongside the original Control Center during comparison tests.
-- No calls to create_resource, create_content, or any data mutation methods.
local function log(msg)
  print("[CC2 OBSERVE] " .. tostring(msg))
end
log("Probe loaded; no mutation commands")
log("Reference rake GUID=f9abaf9b-060c-470d-a8c3-c7c567ebaa1e")
if game == nil or game.assets == nil then
  log("game.assets missing at patch execution; timing/API remains UNSOLVED")
  return
end
local assets = game.assets
log("get_resources_by_type=" .. type(assets.get_resources_by_type))
log("get_resource=" .. type(assets.get_resource))
log("get_resource_parts=" .. type(assets.get_resource_parts))
log("get_resource_types=" .. type(assets.get_resource_types))
log("create_resource=" .. type(assets.create_resource))
log("create_content=" .. type(assets.create_content))
if type(assets.get_resources_by_type) ~= "function" then
  log("No get_resources_by_type callable; stopped")
  return
end
local function count_safely(resources)
  -- EML may expose typed userdata, not a regular Lua array.
  local ok, n = pcall(function()
    local count = 0
    for _ in pairs(resources) do
      count = count + 1
      if count >= 20000 then return count end
    end
    return count
  end)
  if ok then return tostring(n) end
  return "not enumerable without inspecting installed EML type definitions"
end
for _, resource_type in ipairs({
  "keen::ItemInfo", "keen::ItemRegistryResource", "keen::RecipeRegistryResource",
  "keen::ItemKnowledgeResource", "keen::WorkshopRegistryResource"
}) do
  local ok, result = pcall(assets.get_resources_by_type, resource_type)
  if ok then
    log(resource_type .. " returned " .. type(result) .. "; count=" .. count_safely(result))
  else
    log(resource_type .. " lookup error: " .. tostring(result))
  end
end
if type(assets.get_resource) == "function" then
  local ok, result = pcall(assets.get_resource, "f9abaf9b-060c-470d-a8c3-c7c567ebaa1e", "keen::ItemInfo", 0)
  log("rake ItemInfo lookup=" .. (ok and (result == nil and "nil" or type(result)) or ("ERROR " .. tostring(result))))
end
log("Probe completed; record EML build, game build and logs for validation")
