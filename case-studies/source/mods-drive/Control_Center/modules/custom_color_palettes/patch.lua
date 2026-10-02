-- Module: Custom Color Palettes
local Module = {}
function Module.OnInit(config, context)
    if not config.enable_custom_colors then return end
    local col = (context.GetResources('keen::CharacterPresetCollection') or {})[1]
    local presets = col and col.data and col.data.presets
    if not presets then return end

    context.Log('Injected custom color palettes into CharacterPresetCollection.')
end
return Module