-- Module: Custom Hair & Beards
local Module = {}
function Module.OnInit(config, context)
    if not config.enable_custom_hair_beards then return end
    local col = (context.GetResources('keen::CharacterPresetCollection') or {})[1]
    local presets = col and col.data and col.data.presets
    if not presets then return end
    -- Unlock all character preset customization options
    for i, p in ipairs(presets) do
        if p.references then
            p.references.isPlayerCustomizationOption = true
        end
    end

    context.Log('Injected custom hair & beards into active character presets.')
end
return Module