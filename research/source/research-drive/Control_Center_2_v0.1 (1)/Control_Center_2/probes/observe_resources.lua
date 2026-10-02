-- CC2 OBSERVE-ONLY EML research probe. Not automatically deployed by Control Center 2.
-- Only install manually in a confirmed EML-compatible experimental mod.
-- This script never mutates game resources, saves or memory.
local function out(message)
    print("[CC2 OBSERVE] " .. tostring(message))
end
out("Probe started. No mutations requested.")
if type(game) ~= "table" or type(game.assets) ~= "table" then
    out("game.assets unavailable at script execution; runtime API/timing UNSOLVED")
    return
end
out("get_resources_by_type type: " .. type(game.assets.get_resources_by_type))
out("create_resource type: " .. type(game.assets.create_resource))
out("create_content type: " .. type(game.assets.create_content))
if type(game.assets.get_resources_by_type) ~= "function" then
    out("Cannot query resource types; stopping")
    return
end
for _, name in ipairs({"keen::ItemInfo", "keen::ItemRegistryResource", "keen::RecipeRegistryResource"}) do
    local ok, result = pcall(game.assets.get_resources_by_type, name)
    if ok then
        out(name .. " query returned " .. type(result))
        if type(result) == "table" then
            local n = 0
            for _ in pairs(result) do n = n + 1 end
            out(name .. " table entries: " .. tostring(n))
        end
    else
        out(name .. " query failed: " .. tostring(result))
    end
end
out("Probe finished. Runtime observations must be matched to actual game build.")
