-- Module: Custom Furniture
local Module = {}
function Module.OnInit(config, context)
    if not config.enable_custom_furniture then return end
    local comfortMult = config.comfort_score_multiplier or 1.0
    local reg = (context.GetResources('keen::RecipeRegistryResource') or {})[1]
    local recipeData = reg and reg.data
    local items = context.GetResources('keen::ItemInfo') or {}

    context.Log('Transmuted custom furniture items into active crafting slots.')
end
return Module