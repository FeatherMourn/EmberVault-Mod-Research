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

if game == nil or game.assets == nil then
  log("game.assets unavailable")
  export_marker("probe_incomplete", "game.assets unavailable")
  return
end

local assets = game.assets
for _, name in ipairs({
  "get_resources_by_type", "get_resource", "get_resource_parts",
  "get_resource_types"
}) do
  log("assets." .. name .. "=" .. kind(assets[name]))
end

log("world=" .. kind(game.world) .. "; player=" .. kind(game.player) .. "; actions=" .. kind(game.actions))
export_marker("capabilities_observed", "no placement or mutation attempted")
