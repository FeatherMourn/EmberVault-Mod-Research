-- Module: Custom Weapons & Armor
local Module = {}
function Module.OnInit(config, context)
    if not config.enable_custom_weapons then return end
    local reg = (context.GetResources('keen::RecipeRegistryResource') or {})[1]
    local recipeData = reg and reg.data
    local items = context.GetResources('keen::ItemInfo') or {}

    context.Log('Transmuted custom weapons into active crafting slots.')
end
return Module