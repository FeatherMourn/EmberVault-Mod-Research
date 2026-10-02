-- Emberworks Worldwright runtime probe.
-- Observe-only: no resource, world, save, or placement mutation.

local function log(message)
  print("[EMBERWORKS WORLDWRIGHT PROBE] " .. tostring(message))
end

local function kind(value)
  return value == nil and "nil" or type(value)
end

local function export_marker(state, detail)
  if io == nil or type(io.export) ~= "function" then
    log("export unavailable; state=" .. state)
    return
  end
  local escaped = tostring(detail or ""):gsub('"', '\\"')
  local payload = '{"probe":"emberworks_worldwright","state":"' .. state .. '","detail":"' .. escaped .. '"}'
  local ok, err = pcall(io.export, "emberworks_worldwright_probe.json", payload)
  log(ok and "evidence exported" or ("evidence export failed: " .. tostring(err)))
end

log("loaded; observe-only mode")
log("loader=" .. kind(loader) .. "; game=" .. kind(game) .. "; io=" .. kind(io))
if loader ~= nil and loader.features ~= nil then
  for _, name in ipairs({"patch", "export", "runtime"}) do
    log("loader.features." .. name .. "=" .. tostring(loader.features[name]))
  end
  if loader.features.runtime ~= nil then
    log("loader.features.runtime.dll=" .. tostring(loader.features.runtime.dll))
  end
end
if loader ~= nil then
  log("loader.is_client=" .. tostring(loader.is_client) .. "; loader.is_server=" .. tostring(loader.is_server))
  log("loader.has_mod=" .. kind(loader.has_mod))
end

if game == nil or game.assets == nil then
  log("game.assets unavailable")
  export_marker("probe_incomplete", "game.assets unavailable")
  return
end

local assets = game.assets
for _, name in ipairs({
  "get_resources_by_type", "get_resource", "get_resource_parts",
  "get_resource_types", "get_all_resources", "get_content",
  "get_all_contents", "create_resource", "register_resource", "create_content"
}) do
  log("assets." .. name .. "=" .. kind(assets[name]))
end

local function count(value)
  if type(value) ~= "table" then return -1 end
  local n = 0
  for _ in pairs(value) do n = n + 1 end
  return n
end

for _, resource_type in ipairs({
  "keen::ItemInfo",
  "keen::Recipe",
  "keen::VoxelModelResource",
  "keen::RenderModel",
  "keen::BuildableObject"
}) do
  if type(assets.get_resources_by_type) == "function" then
    local ok, result = pcall(assets.get_resources_by_type, resource_type)
    log(resource_type .. "=" .. (ok and tostring(count(result)) or ("error:" .. tostring(result))))
  end
end

log("game.guid=" .. kind(game.guid) .. "; game.version=" .. tostring(game.version or ""))
log("world=" .. kind(game.world) .. "; player=" .. kind(game.player) .. "; actions=" .. kind(game.actions))
export_marker("capabilities_observed", "read-only API inventory; no placement or mutation attempted")
