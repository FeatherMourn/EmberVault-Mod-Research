-- ============================================================================
-- Module: World Rules & Difficulty Tuning (world_and_difficulty)
-- Target: keen::GameSettingsPresetsResource, keen::FbUiBundle
-- ============================================================================

local Module = {}

local function setField(obj, key, val)
    if not obj then return false end
    local ok, applied = pcall(function()
        local f = obj[key]
        if f == nil then return false end
        if type(f) == "userdata" or type(f) == "table" then
            local valueOk, current = pcall(function() return f.value end)
            if valueOk and current ~= nil then
                local writeOk = pcall(function() f.value = val end)
                return writeOk
            end
            return false
        end
        local writeOk = pcall(function() obj[key] = val end)
        return writeOk
    end)
    return ok and applied == true
end

function Module.OnInit(config, context)
    context.Log("Applying World Rules & Game Settings modifications via direct resource lookup...")
    -- Bulk enumeration of this family crosses an unsafe EML boundary. Direct
    -- identity lookup is runtime-verified and avoids the crashing path.
    local SETTINGS_GUID = "46e14df6-fb8f-4f66-9463-e23b9e19e48e"
    local ok, presetRes = pcall(function()
        return game.assets.get_resource(SETTINGS_GUID, "keen::GameSettingsPresetsResource", 0)
    end)
    if not ok or not presetRes or not presetRes.data then
        context.LogWarn("Game settings resource was unavailable; no settings were changed.")
        return
    end
    local uiOk, uiRes = pcall(function()
        return game.assets.get_resource(SETTINGS_GUID, "keen::FbUiBundle", 0)
    end)
    local presetsObj = presetRes.data
    local uiObj = (uiOk and uiRes and uiRes.data) or nil

    local targets = {}
    if presetsObj then
        if presetsObj.minValues then table.insert(targets, presetsObj.minValues) end
        if presetsObj.maxValues then table.insert(targets, presetsObj.maxValues) end
    end

    for _, target in ipairs(targets) do
        -- Combat & Enemies
        if config.enemy_damage_factor then setField(target, "enemyDamageFactor", config.enemy_damage_factor) end
        if config.enemy_health_factor then setField(target, "enemyHealthFactor", config.enemy_health_factor) end
        if config.boss_damage_factor then setField(target, "bossDamageFactor", config.boss_damage_factor) end
        if config.boss_health_factor then setField(target, "bossHealthFactor", config.boss_health_factor) end
        if config.pacify_all_enemies ~= nil then setField(target, "pacifyAllEnemies", config.pacify_all_enemies) end

        -- Progression & XP
        if config.experience_combat_factor then setField(target, "experienceCombatFactor", config.experience_combat_factor) end
        if config.experience_mining_factor then setField(target, "experienceMiningFactor", config.experience_mining_factor) end

        -- Harvesting & Economy
        if config.resource_drop_stack_factor then setField(target, "resourceDropStackAmountFactor", config.resource_drop_stack_factor) end
        if config.mining_damage_factor then setField(target, "miningDamageFactor", config.mining_damage_factor) end
        if config.plant_growth_speed_factor then setField(target, "plantGrowthSpeedFactor", config.plant_growth_speed_factor) end
        if config.factory_production_speed_factor then setField(target, "factoryProductionSpeedFactor", config.factory_production_speed_factor) end

        -- Mechanics & Durability
        if config.disable_durability then setField(target, "enableDurability", false) end
        if config.food_buff_duration_factor then setField(target, "foodBuffDurationFactor", config.food_buff_duration_factor) end
        if config.player_health_factor then setField(target, "playerHealthFactor", config.player_health_factor) end
        if config.player_mana_factor then setField(target, "playerManaFactor", config.player_mana_factor) end
        if config.player_stamina_factor then setField(target, "playerStaminaFactor", config.player_stamina_factor) end
        if config.player_body_heat_factor then setField(target, "playerBodyHeatFactor", config.player_body_heat_factor) end
        if config.player_diving_time_factor then setField(target, "playerDivingTimeFactor", config.player_diving_time_factor) end
        if config.enable_starving_debuff ~= nil then setField(target, "enableStarvingDebuff", config.enable_starving_debuff) end
        if config.shroud_time_factor then setField(target, "shroudTimeFactor", config.shroud_time_factor) end
        if config.enable_glider_turbulences ~= nil then setField(target, "enableGliderTurbulences", config.enable_glider_turbulences) end
        if config.weather_frequency then setField(target, "weatherFrequency", config.weather_frequency) end
        if config.fishing_difficulty then setField(target, "fishingDifficulty", config.fishing_difficulty) end
        if config.enemy_stamina_factor then setField(target, "enemyStaminaFactor", config.enemy_stamina_factor) end
        if config.enemy_perception_range_factor then setField(target, "enemyPerceptionRangeFactor", config.enemy_perception_range_factor) end
        if config.threat_bonus then setField(target, "threatBonus", config.threat_bonus) end
        if config.random_spawner_amount then setField(target, "randomSpawnerAmount", config.random_spawner_amount) end
        if config.aggro_pool_amount then setField(target, "aggroPoolAmount", config.aggro_pool_amount) end
        if config.day_time_duration then setField(target, "dayTimeDuration", config.day_time_duration) end
        if config.night_time_duration then setField(target, "nightTimeDuration", config.night_time_duration) end
        if config.taming_startle_repercussion then setField(target, "tamingStartleRepercussion", config.taming_startle_repercussion) end
        if config.curse_modifier then setField(target, "curseModifier", config.curse_modifier) end
    end

    context.Log("World Rules & Difficulty direct settings applied; preset-array and UI traversal skipped for safety.")
end

return Module
