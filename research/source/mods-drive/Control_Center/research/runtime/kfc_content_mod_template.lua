-- Copy this file into a mod's src/mod.lua and adjust the IDs.
-- Copy kfc_content_registry.lua into the same mod's src/ directory.
local kfc = require('kfc_content_registry')

local DONOR_ITEM_ID = 2940001508
local DONOR_RECIPE_ID = 3531872774
local NEW_ITEM_ID = 3987654321
local NEW_RECIPE_ID = 3987654322

local item_registry
for _, resource in pairs(kfc.resources('keen::ItemRegistryResource')) do
    if resource.data and resource.data.itemRefs then item_registry = resource; break end
end
local recipe_registry = kfc.resources('keen::RecipeRegistryResource')[1]
local donor = kfc.find_by_value('keen::ItemInfo', 'itemId', DONOR_ITEM_ID)
if not donor or not recipe_registry then return {} end

local clone = kfc.clone_resource(donor, 'keen::ItemInfo')
clone.data.itemId.value = NEW_ITEM_ID
clone.data.debugName = 'CC_Custom_Content'
kfc.append_registry(item_registry, 'itemRefs', clone)

local donor_recipe
for _, recipe in pairs(recipe_registry.data.recipes or {}) do
    for _, output in pairs(recipe.output or {}) do
        if output.item and output.item.value == DONOR_ITEM_ID then donor_recipe = recipe; break end
    end
    if donor_recipe then break end
end
if donor_recipe then
    local recipe = kfc.deep_copy(donor_recipe)
    recipe.recipeId.value = NEW_RECIPE_ID
    for _, output in pairs(recipe.output or {}) do
        if output.item then output.item.value = NEW_ITEM_ID end
        if output.itemRef then output.itemRef = clone.guid end
    end
    kfc.append_registry(recipe_registry, 'recipes', recipe)
end

local ui = kfc.resources('keen::FbUiBundle')[1]
if ui then kfc.clone_recipe_set(ui, DONOR_RECIPE_ID, NEW_RECIPE_ID) end
return {}
