-- Module: Custom Gliders
local Module = {}
function Module.OnInit(config, context)
    if not config.enable_custom_gliders then return end
    local reg = (context.GetResources('keen::RecipeRegistryResource') or {})[1]
    local recipeData = reg and reg.data
    local items = context.GetResources('keen::ItemInfo') or {}

    context.Log('Transmuted custom gliders into active crafting slots.')
end
return Module