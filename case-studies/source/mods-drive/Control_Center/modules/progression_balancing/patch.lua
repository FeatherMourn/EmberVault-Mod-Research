-- ============================================================================
-- Module: Progression & Character Balancing (progression_balancing)
-- Target: keen::BalancingTable
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Progression & Character Balancing modifications...")

    local tables = context.GetResources("keen::BalancingTable")
    if not tables or #tables == 0 then
        context.LogWarn("No keen::BalancingTable resources found!")
        return
    end

    for _, res in ipairs(tables) do
        local d = res and res.data
        if d then
            -- 1. Level Caps
            if config.player_level_cap and config.player_level_cap > 25 then
                d.playerLevelCap = config.player_level_cap
                d.playerLevelMax = math.max(d.playerLevelMax or 25, config.player_level_cap)
            end

            if config.item_level_cap and config.item_level_cap > 50 then
                d.itemLevelCap = config.item_level_cap
            end

            -- 2. Shroud Fog Resistance (Timer)
            if config.shroud_fog_resistance_multiplier and config.shroud_fog_resistance_multiplier > 1.0 then
                local baseFog = d.playerBaseFogResistance or 300
                d.playerBaseFogResistance = math.floor(baseFog * config.shroud_fog_resistance_multiplier)
            end

            -- 3. Base Attribute Pools
            if config.player_base_health and config.player_base_health > 100 then
                d.playerBaseHealth = config.player_base_health
            end

            if config.player_base_stamina and config.player_base_stamina > 100 then
                d.playerBaseStamina = config.player_base_stamina
            end

            if config.player_base_mana and config.player_base_mana > 100 then
                d.playerBaseMana = config.player_base_mana
            end

            -- 4. Progression Rates
            if config.skill_points_per_level and config.skill_points_per_level > 1 then
                d.skillPointsPerLevel = config.skill_points_per_level
            end

            if config.ap_per_flame_level and config.ap_per_flame_level > 1 then
                d.apPerFlameLevel = config.ap_per_flame_level
            end

            -- 5. Critical Hits
            if config.base_crit_chance then
                d.baseCritChance = config.base_crit_chance / 100.0
            end

            if config.crit_bonus_multiplier and config.crit_bonus_multiplier > 1.5 then
                d.critBonus = config.crit_bonus_multiplier
            end

            -- 6. Altars
            if config.altars_per_flame_level and config.altars_per_flame_level > 1 and d.altarsPerFlameLevel then
                for i = 1, #d.altarsPerFlameLevel do
                    d.altarsPerFlameLevel[i] = math.min(255, config.altars_per_flame_level)
                end
            end

            context.Log("Patched keen::BalancingTable (GUID: " .. tostring(res.guid) .. ") successfully!")
        end
    end
end

return Module
