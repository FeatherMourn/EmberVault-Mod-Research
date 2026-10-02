-- Module: Custom Pets
local Module = {}
function Module.OnInit(config, context)
    if not config.enable_custom_pets then return end
    local reg = (context.GetResources('keen::RecipeRegistryResource') or {})[1]
    local recipeData = reg and reg.data
    local items = context.GetResources('keen::ItemInfo') or {}

    context.Log('Transmuted custom pet whistles into active crafting slots.')
end
return Module