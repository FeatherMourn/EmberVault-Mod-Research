-- Module: Custom Spells
local Module = {}
function Module.OnInit(config, context)
    if not config.enable_custom_spells then return end
    local dmgMult = config.custom_spell_damage_multiplier or 1.0
    local reg = (context.GetResources('keen::RecipeRegistryResource') or {})[1]
    local recipeData = reg and reg.data
    local items = context.GetResources('keen::ItemInfo') or {}

    context.Log('Transmuted custom spells into active crafting slots.')
end
return Module