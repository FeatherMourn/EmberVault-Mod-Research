-- ============================================================================
-- Module: Terraforming, Mining & Flora Density (terraforming_and_mining)
-- Target: keen::TerraformingEfficiencyRegistryResource
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Terraforming & Mining Efficiency modifications...")

    local terraList = context.GetResources("keen::TerraformingEfficiencyRegistryResource")
    if not terraList or #terraList == 0 then
        context.LogWarn("No keen::TerraformingEfficiencyRegistryResource found!")
        return
    end

    if config.terraforming_speed_multiplier and config.terraforming_speed_multiplier > 1.0 then
        for _, res in ipairs(terraList) do
            local d = res and res.data
            if d and d.terrainConfigs and type(d.terrainConfigs) == "table" then
                for _, cfg in ipairs(d.terrainConfigs) do
                    if cfg.efficiency then
                        cfg.efficiency = cfg.efficiency * config.terraforming_speed_multiplier
                    end
                end
            end
        end
        context.Log("Multiplied terraforming voxel efficiency by " .. tostring(config.terraforming_speed_multiplier) .. "x!")
    end
end

return Module
