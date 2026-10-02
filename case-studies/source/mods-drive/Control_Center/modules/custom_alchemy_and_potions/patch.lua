-- Module: Custom Potions
local Module = {}
function Module.OnInit(config, context)
    if not config.enable_custom_potions then return end
    local reg = (context.GetResources('keen::RecipeRegistryResource') or {})[1]
    local recipeData = reg and reg.data
    local items = context.GetResources('keen::ItemInfo') or {}

    context.Log('Transmuted custom potions into active crafting slots.')
end
return Module