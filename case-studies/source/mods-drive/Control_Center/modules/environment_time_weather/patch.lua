-- ============================================================================
-- Module: Environment, Night Vision & Lighting (environment_time_weather)
-- Target: keen::AmbientPostProcessingResource
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Ambient & Post-Processing Environment modifications...")

    local postResList = context.GetResources("keen::AmbientPostProcessingResource")
    if not postResList or #postResList == 0 then
        context.LogWarn("No keen::AmbientPostProcessingResource found!")
        return
    end

    for _, res in ipairs(postResList) do
        local pp = res and res.data
        if pp then
            -- 1. Night Adaptation / Vision Boost
            if config.night_illumination_boost and config.night_illumination_boost > 1.0 then
                if pp.nightAdaptationStrength then
                    pp.nightAdaptationStrength = pp.nightAdaptationStrength * config.night_illumination_boost
                end
            end

            -- 2. Weather Saturation
            if config.rain_saturation_boost then
                pp.rainWeatherSaturation = config.rain_saturation_boost
            end

            -- 3. Death Filter
            if config.disable_death_screen_desaturation then
                pp.deathScreenSaturation = 1.0
                pp.deathOnlyDesaturates = false
            end
        end
    end

    context.Log("Ambient lighting & night adaptation configured successfully!")
end

return Module
