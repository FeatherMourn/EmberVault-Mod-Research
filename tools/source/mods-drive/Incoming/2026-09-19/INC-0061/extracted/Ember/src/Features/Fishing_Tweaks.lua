local function ApplyFishingTweaks()
    feature_begin("Fishing Tweaks")

    if not Enable_Fishing_Tweaks then
        feature_end(false)
        return
    end

    local targetGuid = "82706b40-61b1-4b8f-8b23-dcec6971bda1"
    local resources = game.assets.get_resources_by_type("keen::BalancingTable")
    local foundResource = nil

    if resources then
        for _, res in ipairs(resources) do
            if tostring(res.guid) == targetGuid then
                foundResource = res
                break
            end
        end
    end

    if not foundResource then
        log_line("ERROR: Could not find Fishing BalancingTable with GUID: " .. targetGuid, 1)
        feature_end(false)
        return
    end

    if not foundResource.data or not foundResource.data.fishingDifficultySettings then
        log_line("ERROR: Resource found but missing fishingDifficultySettings data.", 1)
        feature_end(false)
        return
    end

    local settingsList = foundResource.data.fishingDifficultySettings.settingsPerDifficulty
    if not settingsList then
        log_line("ERROR: settingsPerDifficulty array is missing.", 1)
        feature_end(false)
        return
    end

    local function patch_if_not_nil(targetTable, fieldName, newValue, context)
        if newValue ~= nil then
            if targetTable[fieldName] ~= newValue then
                log_line(string.format("%s: %s -> %s", context, tostring(targetTable[fieldName]), tostring(newValue)), 1)
                targetTable[fieldName] = newValue
                return true
            end
        end
        return false
    end

    local didWork = false

    for i = 1, 5 do
        local gameSettings = settingsList[i]

        if gameSettings then
            local prefix = "Tier" .. i

            local strength = _G[prefix .. "_RodStrength"]
            local endurance = _G[prefix .. "_RodEndurance"]
            local qte = _G[prefix .. "_QuickTimeEvent"]
            local advanced = _G[prefix .. "_AdvancedGame"]
            local reduce = _G[prefix .. "_ReduceRoundsBy"]

            local context = "Tier " .. i

            local changed = false
            changed = patch_if_not_nil(gameSettings, "rodStrengthFactor", strength, context .. " Strength") or changed
            changed = patch_if_not_nil(gameSettings, "rodEnduranceFactor", endurance, context .. " Endurance") or changed
            changed = patch_if_not_nil(gameSettings, "quickTimeEventFactor", qte, context .. " QTE") or changed
            changed = patch_if_not_nil(gameSettings, "isAdvancedMinigameSupported", advanced, context .. " AdvGame") or changed
            changed = patch_if_not_nil(gameSettings, "reduceNumberOfRoundsBy", reduce, context .. " ReduceRounds") or changed

            if changed then didWork = true end
        else
            log_line("WARN: Tier " .. i .. " settings missing in game resource.", 1)
        end
    end

    feature_end(didWork)
end

return ApplyFishingTweaks
