local function log(message)
  print("[EMBERWORKS UI PROBE] " .. tostring(message))
end

local bundles_ok, bundles = pcall(game.assets.get_resources_by_type, "keen::FbUiBundle")
local bundle_count, tree_count, group_count, set_count, entry_count = 0, 0, 0, 0, 0
local recipe_hits = 0
if bundles_ok and type(bundles) == "table" then
  for _, bundle in ipairs(bundles) do
    bundle_count = bundle_count + 1
    local recipes = bundle.data and bundle.data.menu and bundle.data.menu.crafting and bundle.data.menu.crafting.recipes
    if recipes and recipes.trees then
      for _, tree in ipairs(recipes.trees) do
        tree_count = tree_count + 1
        if tree.groups then
          for _, group in ipairs(tree.groups) do
            group_count = group_count + 1
            if group.sets then
              for _, set in ipairs(group.sets) do
                set_count = set_count + 1
                if set.entries then
                  for _, entry in ipairs(set.entries) do
                    entry_count = entry_count + 1
                    local value = entry.value or entry
                    if value == 4294960002 then recipe_hits = recipe_hits + 1 end
                  end
                end
              end
            end
          end
        end
      end
    end
  end
end
log("bundles=" .. bundle_count .. ";trees=" .. tree_count .. ";groups=" .. group_count .. ";sets=" .. set_count .. ";entries=" .. entry_count .. ";probe_recipe_hits=" .. recipe_hits)
if io and type(io.export) == "function" then
  pcall(io.export, "emberworks_ui_probe.json", '{"bundles":' .. bundle_count .. ',"trees":' .. tree_count .. ',"groups":' .. group_count .. ',"sets":' .. set_count .. ',"entries":' .. entry_count .. ',"probe_recipe_hits":' .. recipe_hits .. '}')
end
