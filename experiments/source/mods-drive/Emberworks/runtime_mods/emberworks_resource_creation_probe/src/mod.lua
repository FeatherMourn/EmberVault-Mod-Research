local function log(message)
  print("[EMBERWORKS RESOURCE CREATION PROBE] " .. tostring(message))
end

local function export_marker(state, detail)
  if io == nil or type(io.export) ~= "function" then return end
  local escaped = tostring(detail or ""):gsub('"', '\\"')
  pcall(io.export, "emberworks_resource_creation_probe.json",
    '{"probe":"emberworks_resource_creation","state":"' .. state .. '","detail":"' .. escaped .. '"}')
end

if game == nil or game.assets == nil or type(game.assets.get_resources_by_type) ~= "function" then
  log("asset API unavailable")
  export_marker("inconclusive", "asset API unavailable")
  return
end

local ok, resources = pcall(game.assets.get_resources_by_type, "keen::ItemInfo")
if not ok or type(resources) ~= "table" or resources[1] == nil then
  log("ItemInfo donor unavailable")
  export_marker("inconclusive", "ItemInfo donor unavailable")
  return
end

if type(game.assets.create_resource) ~= "function" then
  log("create_resource unavailable")
  export_marker("unsupported", "create_resource unavailable")
  return
end

local created, result = pcall(game.assets.create_resource, resources[1].data, "keen::ItemInfo")
log("create_resource_result=" .. tostring(created) .. "; result_type=" .. type(result))
local registered = false
if created and result ~= nil and result.data ~= nil and result.data.itemId ~= nil then
  local assigned_id = 4294960001
  local id_ok = pcall(function() result.data.itemId.value = assigned_id end)
  local registry_ok, registries = pcall(game.assets.get_resources_by_type, "keen::ItemRegistryResource")
  local main_registry = nil
  local main_count = -1
  if registry_ok and type(registries) == "table" then
    for _, registry in ipairs(registries) do
      local count = 0
      for _ in ipairs(registry.data.itemRefs) do count = count + 1 end
      if count > main_count then main_registry = registry; main_count = count end
    end
  end
  if id_ok and main_registry ~= nil then
    registered = pcall(function() table.insert(main_registry.data.itemRefs, result) end)
  end
  log("item_registry_insert_result=" .. tostring(registered) .. "; assigned_id=" .. tostring(assigned_id))
end

local recipe_registered = false
local recipe_ok, recipe_registries = pcall(game.assets.get_resources_by_type, "keen::RecipeRegistryResource")
if recipe_ok and type(recipe_registries) == "table" and recipe_registries[1] ~= nil and created and result ~= nil then
  local recipe_registry = recipe_registries[1]
  local donor_recipe = recipe_registry.data.recipes[1]
  if donor_recipe ~= nil then
    local insert_ok, inserted = pcall(function()
      table.insert(recipe_registry.data.recipes, donor_recipe)
      return recipe_registry.data.recipes[#recipe_registry.data.recipes]
    end)
    if insert_ok and inserted ~= nil then
      recipe_registered = pcall(function()
        inserted.recipeId.value = 4294960002
        inserted.debugName = "Emberworks_Resource_Creation_Probe_Recipe"
        if inserted.output[1] ~= nil then
          inserted.output[1].item.value = 4294960001
          inserted.output[1].itemRef = result
          inserted.output[1].count = 1
        end
      end)
    end
  end
end
log("recipe_registry_insert_result=" .. tostring(recipe_registered))

local ui_hits = 0
local ui_ok, ui_bundles = pcall(game.assets.get_resources_by_type, "keen::FbUiBundle")
local ui_scan_ok, ui_scan_error = pcall(function()
  if ui_ok and type(ui_bundles) == "table" then
    for _, bundle in ipairs(ui_bundles) do
      local recipes = bundle.data and bundle.data.menu and bundle.data.menu.crafting and bundle.data.menu.crafting.recipes
      if recipes and recipes.trees then
        for _, tree in ipairs(recipes.trees) do
          if tree.groups then
            for _, group in ipairs(tree.groups) do
              if group.sets then
                for _, set in ipairs(group.sets) do
                  if set.entries then
                    for _, entry in ipairs(set.entries) do
                      if (entry.value or entry) == 4294960002 then ui_hits = ui_hits + 1 end
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
end)
log("ui_recipe_link_hits=" .. tostring(ui_hits) .. ";scan_ok=" .. tostring(ui_scan_ok) .. ";scan_error=" .. tostring(ui_scan_error))

local voxel_ok, voxels = pcall(game.assets.get_resources_by_type, "keen::VoxelModelResource")
local voxel_created, voxel_result = false, nil
if voxel_ok and type(voxels) == "table" and voxels[1] ~= nil then
  voxel_created, voxel_result = pcall(game.assets.create_resource, voxels[1].data, "keen::VoxelModelResource")
  log("voxel_create_result=" .. tostring(voxel_created) .. "; result_type=" .. type(voxel_result))
end

local render_created = false
if voxel_created and type(game.assets.get_resources_by_type) == "function" then
  local render_ok, renders = pcall(game.assets.get_resources_by_type, "keen::RenderModel")
  if render_ok and type(renders) == "table" and renders[1] ~= nil then
    render_created = pcall(game.assets.create_resource, renders[1].data, "keen::RenderModel", voxel_result.guid, 0)
    log("render_create_result=" .. tostring(render_created))
  end
end

export_marker(created and "created_unreferenced_resource" or "creation_failed",
  "item=" .. tostring(created) .. ";registered=" .. tostring(registered) .. ";recipe=" .. tostring(recipe_registered) .. ";ui_hits=" .. tostring(ui_hits) .. ";voxel=" .. tostring(voxel_created) .. ";render=" .. tostring(render_created))
