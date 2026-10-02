-- ========================================
--          EXPANDED GAME SETTINGS
-- ========================================

local function ApplyExpandedGameSettings()
    feature_begin("Expanded Game Settings")

    if not Enable_ExpandedGameSettings then
        log_line("Feature Disabled check Config")
        feature_end(false)
        return
    end

    local level = 1
    local function logInfo(msg) log_line(msg, level) end
    local function logWarn(msg) log_line("WARN: " .. tostring(msg), level) end
    local function logError(msg) log_line("ERROR: " .. tostring(msg), level) end

    -- ========================================
    --            CALCULATION HELPER
    -- ========================================

    local function generateRange(startNum, stopNum, count)
        local steps = {}
        if count > 32 then
            logWarn(string.format("Request for %d steps exceeds safety limit (32). Clamping to 32.", count))
            count = 32
        end
        if count < 2 then count = 2 end

        local stepSize = (stopNum - startNum) / (count - 1)
        for i = 0, count - 2 do
            local val = startNum + (i * stepSize)
            val = math.floor(val * 100 + 0.5) / 100
            table.insert(steps, val)
        end
        table.insert(steps, stopNum)
        return steps
    end

    local presets_res = get_first_resource_by_type("keen::GameSettingsPresetsResource")
    local ui_res = get_first_resource_by_type("keen::FbUiBundle")

    if not presets_res or not ui_res then
        logError("Required resources not found (GameSettingsPresetsResource or FbUiBundle)")
        feature_end(false)
        return
    end

    local VALID_GAME_SETTINGS = {
        playerHealthFactor = true,
        playerManaFactor = true,
        playerStaminaFactor = true,
        playerBodyHeatFactor = true,
        playerDivingTimeFactor = true,
        enableDurability = true,
        -- enableStarvingDebuff = true,
        foodBuffDurationFactor = true,
        fromHungerToStarving = true,
        shroudTimeFactor = true,
        -- tombstoneMode = true,
        -- enableGliderTurbulences = true,
        weatherFrequency = true,
        fishingDifficulty = true,
        miningDamageFactor = true,
        plantGrowthSpeedFactor = true,
        resourceDropStackAmountFactor = true,
        factoryProductionSpeedFactor = true,
        perkUpgradeRecyclingFactor = true,
        perkCostFactor = true,
        experienceCombatFactor = true,
        experienceMiningFactor = true,
        experienceExplorationQuestsFactor = true,
        randomSpawnerAmount = true,
        aggroPoolAmount = true,
        enemyDamageFactor = true,
        enemyHealthFactor = true,
        enemyStaminaFactor = true,
        enemyPerceptionRangeFactor = true,
        bossDamageFactor = true,
        bossHealthFactor = true,
        threatBonus = true,
        -- pacifyAllEnemies = true,
        tamingStartleRepercussion = true,
        dayTimeDuration = true,
        nightTimeDuration = true,
        curseModifier = true,
    }

    local presets = presets_res.data
    local ui = ui_res.data

    local ConfigEnabledMap = {}
    if ExpandedGameSettings_Config and type(ExpandedGameSettings_Config) == "table" then
        for _, cfg in ipairs(ExpandedGameSettings_Config) do
            if cfg.Name then
                local isEnabled = true
                if cfg.Enabled ~= nil then isEnabled = cfg.Enabled end
                ConfigEnabledMap[cfg.Name] = isEnabled
            end
        end
    end

    local OverrideDependencies = {
        ["fromHungerToStarving"] = "starvingTime",
        ["dayTimeDuration"] = "dayTime",
        ["nightTimeDuration"] = "nightTime",
    }

    local UnsupportedConfigSettings = {
        ["durability"] = "current dumps expose boolean enableDurability, not a scalar durability range",
    }

    local ConfigToPresetMap = {
        -- [PLAYER]
        ["playerHealth"]     = "playerHealthFactor",
        ["playerMana"]       = "playerManaFactor",
        ["playerStamina"]    = "playerStaminaFactor",
        ["bodyHeat"]         = "playerBodyHeatFactor",

        -- [SURVIVAL]
        ["foodDuration"]     = "foodBuffDurationFactor",
        ["starvingTime"]     = "fromHungerToStarving",
        ["playerDivingTime"] = "playerDivingTimeFactor",
        ["shroudTime"]       = "shroudTimeFactor",

        -- [WORLD]
        ["miningDamage"]     = "miningDamageFactor",
        ["plantGrowTime"]    = "plantGrowthSpeedFactor",
        ["dropAmount"]       = "resourceDropStackAmountFactor",
        ["productionTime"]   = "factoryProductionSpeedFactor",

        -- [COMBAT]
        ["weaponUpgradeCost"] = "perkCostFactor",
        ["perkUpgradeRecyclingFactor"] = "perkUpgradeRecyclingFactor",
        ["enableDurability"] = "enableDurability",

        -- [XP]
        ["combatXp"]  = "experienceCombatFactor",
        ["miningXp"]  = "experienceMiningFactor",
        ["questXp"]   = "experienceExplorationQuestsFactor",

        -- [ENEMY]
        ["enemyDamage"]          = "enemyDamageFactor",
        ["enemyHealth"]          = "enemyHealthFactor",
        ["enemyStamina"]         = "enemyStaminaFactor",
        ["enemyPerceptionRange"] = "enemyPerceptionRangeFactor",
        ["enemyAttackFrequency"] = "aggroPoolAmount",

        -- [BOSS]
        ["bossDamage"] = "bossDamageFactor",
        ["bossHealth"] = "bossHealthFactor",

        -- [TIME]
        ["dayTime"]   = "dayTimeDuration",
        ["nightTime"] = "nightTimeDuration",
    }

    local function SafeSetPreset(key, min, max)
        if not VALID_GAME_SETTINGS[key] then
            return false
        end

        local applied = false
        local ok, err = pcall(function()
            if presets.minValues[key] == nil then
                return
            end

            local field = presets.minValues[key]
            if type(field) == "userdata" or type(field) == "table" then
                local s_field = tostring(field)
                if string.find(s_field, "ValueWrapper") or field.value ~= nil then
                    field.value = min
                    applied = true
                else
                    log_line("WARN: Complex type for " .. key .. " not fully supported.", 1)
                end
            else
                presets.minValues[key] = min
                applied = true
            end

            if presets.maxValues[key] ~= nil then
                local fieldMax = presets.maxValues[key]
                if type(fieldMax) == "userdata" or type(fieldMax) == "table" then
                    if fieldMax.value ~= nil then fieldMax.value = max end
                else
                    presets.maxValues[key] = max
                end
            end
        end)

        if not ok then
            logError("Error setting preset " .. key .. ": " .. tostring(err))
            return false
        end
        return applied
    end
    local function SetBooleanSetting(settingName, value, presetOverride)
        if not ui.difficultySettings or not ui.difficultySettings.settingValues then
            logError("ui.difficultySettings.settingValues not found.")
            return
        end

        local backendKeys = {}

        if ConfigToPresetMap[settingName] then
            table.insert(backendKeys, ConfigToPresetMap[settingName])
        end

        if presetOverride then
            table.insert(backendKeys, presetOverride)
        end

        table.insert(backendKeys, settingName)

        local applied = false
        for _, key in ipairs(backendKeys) do
            if SafeSetPreset(key, value, value) then
                logInfo(string.format(
                    "SUCCESS: Mapped Config '%s' -> Backend '%s' [%s]",
                    settingName, key, tostring(value)
                ))
                applied = true
                break
            end
        end

        if ui.difficultySettings.settingValues[settingName] ~= nil then
            ui.difficultySettings.settingValues[settingName] = value
            logInfo("Updated UI boolean for '" .. tostring(settingName) .. "' = " .. tostring(value))
        else
            logError("UI Setting not found: " .. tostring(settingName))
        end

        if not applied then
            log_line(
                "WARN: Could not map Config '" .. settingName .. "' to any valid GameSettings key. Checked: " ..
                table.concat(backendKeys, ", "),
                1
            )
        end
    end
    local function SetScalarRange(settingName, startVal, stopVal, count, presetOverride)
        if not ui.difficultySettings or not ui.difficultySettings.settingValues then
            logError("ui.difficultySettings.settingValues not found.")
            return
        end

        local newSteps = generateRange(startVal, stopVal, count)

        if ui.difficultySettings.settingValues[settingName] then
            ui.difficultySettings.settingValues[settingName].steps = newSteps
            logInfo(string.format(
                "Updated UI steps for '%s' (%d steps): %.2f -> %.2f",
                settingName, #newSteps, startVal, stopVal
            ))
        else
            logError("UI Setting not found: " .. tostring(settingName))
        end

        local min = math.min(startVal, stopVal)
        local max = math.max(startVal, stopVal)

        local backendMin, backendMax = min, max
        if settingName == "dayTime" or settingName == "nightTime" then
            local SEC = 1e9
            backendMin = min * 60 * SEC
            backendMax = max * 60 * SEC
        end

        local backendKeys = {}

        if ConfigToPresetMap[settingName] then
            table.insert(backendKeys, ConfigToPresetMap[settingName])
        end

        if presetOverride then
            table.insert(backendKeys, presetOverride)
        end

        table.insert(backendKeys, settingName .. "Factor")

        table.insert(backendKeys, settingName)

        local applied = false
        for _, key in ipairs(backendKeys) do
            if SafeSetPreset(key, backendMin, backendMax) then
                logInfo(string.format(
                    "SUCCESS: Mapped Config '%s' -> Backend '%s' [%s, %s]",
                    settingName, key, tostring(backendMin), tostring(backendMax)
                ))
                applied = true
                break
            end
        end

        if not applied then
            log_line(
                "WARN: Could not map Config '" .. settingName .. "' to any valid GameSettings key. Checked: " ..
                table.concat(backendKeys, ", "),
                1
            )
        end

        do return end
    end

local function ApplySpecificOverrides()
    local SEC = 1e9
    local HOUR = 60 * 60 * SEC


        local min_overrides = {
            ["experienceCombatFactor"] = 0.0,
            ["experienceMiningFactor"] = 0.0,
            ["experienceExplorationQuestsFactor"] = 0.0,
            ["dayTimeDuration"] = 60 * SEC,
            ["nightTimeDuration"] = 60 * SEC,
            ["fromHungerToStarving"] = 60 * SEC,
        }

        local max_overrides = {
            ["dayTimeDuration"] = 10 * HOUR,
            ["nightTimeDuration"] = 10 * HOUR,
            ["fromHungerToStarving"] = 5 * HOUR,
        }

        logInfo("Applying specific limits overrides...")


        local function SafeSetOne(tbl, key, val)
             if not VALID_GAME_SETTINGS[key] then return end

             local configName = OverrideDependencies[key]
             if configName then
                 local enabled = ConfigEnabledMap[configName]
                 if enabled == false then
                     logInfo("  Skipping override for " .. key .. " (Disabled in Config: " .. configName .. ")")
                     return
                 end
             end

             local ok, err = pcall(function()
                 if tbl[key] ~= nil then
                    local field = tbl[key]
                    if type(field) == "userdata" or type(field) == "table" then
                        if field.value ~= nil then field.value = val end
                    else
                        tbl[key] = val
                    end
                    logInfo("  Override " .. key .. " = " .. tostring(val))
                 end
             end)
        end

        for k, v in pairs(min_overrides) do SafeSetOne(presets.minValues, k, v) end
        for k, v in pairs(max_overrides) do SafeSetOne(presets.maxValues, k, v) end
    end

    local function SetPercentRange(settingName, startPercent, stopPercent, count, presetOverride)
        SetScalarRange(settingName, startPercent / 100.0, stopPercent / 100.0, count, presetOverride)
    end

    local function Setup(params)
        if not params or not params.Name then return end

        local name = params.Name

        if params.Enabled == false then
            logInfo("Skipping disabled setting: " .. tostring(name))
            return
        end

        if UnsupportedConfigSettings[name] then
            logWarn("Skipping unsupported setting '" .. tostring(name) .. "': " .. UnsupportedConfigSettings[name])
            return
        end

        local min = params.Min or 10
        local max = params.Max or 1000
        local steps = params.Steps or 20
        local type_ = params.Type or "Percent"

        local ok, err = pcall(function()
            if type_ == "Boolean" then
                SetBooleanSetting(name, params.Value == true, params.Preset)
            elseif type_ == "Scalar" then
                SetScalarRange(name, min, max, steps, params.Preset)
            else
                SetPercentRange(name, min, max, steps, params.Preset)
            end
        end)
        if not ok then
            logError("Failed to setup " .. tostring(name) .. ": " .. tostring(err))
        end
    end

    local ok, err = pcall(function()
        ApplySpecificOverrides()

        log_line("Applying Enhanced Sliders...")

        if ExpandedGameSettings_Config and type(ExpandedGameSettings_Config) == "table" then
            for _, cfg in ipairs(ExpandedGameSettings_Config) do
                Setup(cfg)
            end
        else
            logError("ExpandedGameSettings_Config not found or invalid.")
        end

    end)

    if not ok then
        logError("Critical error in ApplyExpandedGameSettings: " .. tostring(err))
        feature_end(false)
    else
        feature_end(true)
    end
end

return ApplyExpandedGameSettings
