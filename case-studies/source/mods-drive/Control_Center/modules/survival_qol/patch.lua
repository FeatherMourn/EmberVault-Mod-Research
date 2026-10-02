-- ============================================================================
-- Module: Survival QoL & Utility (survival_qol)
-- Author: JoelT
-- Engine Resource Mappings verified against Keen KFC GameSettings
-- ============================================================================

local Module = {}

local function setPresetValue(container, key, val)
    if not container then return false end
    local ok, applied = pcall(function()
        local field = container[key]
        if field == nil then return false end
        if type(field) == "userdata" or type(field) == "table" then
            local valueOk, current = pcall(function() return field.value end)
            if valueOk and current ~= nil then
                local writeOk = pcall(function() field.value = val end)
                return writeOk
            end
            return false
        end
        local writeOk = pcall(function() container[key] = val end)
        return writeOk
    end)
    return ok and applied == true
end

function Module.OnInit(config, context)
    context.Log("Initializing Survival QoL...")

    -- 1. Stack Size Tweaks (keen::ItemInfo -> maxStackSize)
    if config.stack_multiplier and config.stack_multiplier > 1 then
        local items = context.GetResources("keen::ItemInfo")
        local changed = 0
        for _, it in ipairs(items) do
            local d = it and it.data
            local cur = d and d.maxStackSize
            if type(cur) == "number" and cur > 1 then
                d.maxStackSize = math.min(65535, math.floor(cur * config.stack_multiplier))
                changed = changed + 1
            end
        end
        context.Log("Updated maxStackSize for " .. tostring(changed) .. " items!")
    end

    -- 2. Shroud Timer Multiplier (keen::BalancingTable -> playerBaseFogResistance)
    if config.shroud_time_multiplier and config.shroud_time_multiplier > 1 then
        local TARGET_BALANCING_GUID = "82706b40-61b1-4b8f-8b23-dcec6971bda1"
        local balancingTables = context.GetResources("keen::BalancingTable")
        for _, res in ipairs(balancingTables) do
            if tostring(res.guid) == TARGET_BALANCING_GUID and res.data then
                local base = res.data.playerBaseFogResistance or 300
                res.data.playerBaseFogResistance = base * config.shroud_time_multiplier
                context.Log("Shroud Time multiplied: " .. tostring(base) .. " -> " .. tostring(res.data.playerBaseFogResistance))
                break
            end
        end
    end

    -- 3. Game Settings Tweaks (Stamina & Durability via GameSettingsPresetsResource & FbUiBundle)
    local presetResList = context.GetResources("keen::GameSettingsPresetsResource")
    local uiResList = context.GetResources("keen::FbUiBundle")

    if presetResList and #presetResList > 0 and presetResList[1].data then
        local presets = presetResList[1].data
        local ui = (uiResList and #uiResList > 0 and uiResList[1].data) or nil

        -- Infinite Durability Toggle
        if config.infinite_durability then
            setPresetValue(presets.minValues, "enableDurability", false)
            setPresetValue(presets.maxValues, "enableDurability", false)
            if ui and ui.difficultySettings and ui.difficultySettings.settingValues then
                ui.difficultySettings.settingValues["enableDurability"] = false
            end
            context.Log("GameSettings: Durability loss DISABLED.")
        end

        -- Stamina Drain Reduction / Zero Stamina
        if config.stamina_cost_reduction and config.stamina_cost_reduction > 0 then
            -- 0.0 = zero stamina consumption
            local staminaFactor = math.max(0.0, 1.0 - (config.stamina_cost_reduction / 100.0))
            if config.stamina_cost_reduction >= 100 then
                staminaFactor = 0.0
            end
            setPresetValue(presets.minValues, "playerStaminaFactor", staminaFactor)
            setPresetValue(presets.maxValues, "playerStaminaFactor", staminaFactor)
            if ui and ui.difficultySettings and ui.difficultySettings.settingValues then
                ui.difficultySettings.settingValues["playerStamina"] = staminaFactor
            end
            context.Log("GameSettings: playerStaminaFactor set to " .. tostring(staminaFactor))
        end
    end
end

return Module
