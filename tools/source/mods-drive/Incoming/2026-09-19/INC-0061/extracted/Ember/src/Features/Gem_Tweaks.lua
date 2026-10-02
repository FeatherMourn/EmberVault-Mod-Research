local function ApplyGemTweaks()
    feature_begin("Gem Tweaks", 1)

    if not Enable_GemTweaks then
        feature_end(false)
        return
    end

    local salvageRate = GemTweaks_SalvageRate
    local commonRate = GemTweaks_Probability_Common
    local uncommonRate = GemTweaks_Probability_Uncommon
    local rareRate = GemTweaks_Probability_Rare
    local epicRate = GemTweaks_Probability_Epic
    local legendaryRate = GemTweaks_Probability_Legendary

    local maxClamp = 1.0
    local minClamp = 0.0

    if salvageRate > maxClamp then
        log_line(("WARN: GemTweaks_SalvageRate (%s) > clamp (%s); clamping"):format(tostring(salvageRate), tostring(maxClamp)), 1)
        salvageRate = maxClamp
    end
    if commonRate > maxClamp then
        log_line(("WARN: GemTweaks_Probability_Common (%s) > clamp (%s); clamping"):format(tostring(commonRate), tostring(maxClamp)), 1)
        commonRate = maxClamp
    end
    if uncommonRate > maxClamp then
        log_line(("WARN: GemTweaks_Probability_Uncommon (%s) > clamp (%s); clamping"):format(tostring(uncommonRate), tostring(maxClamp)), 1)
        uncommonRate = maxClamp
    end
    if rareRate > maxClamp then
        log_line(("WARN: GemTweaks_Probability_Rare (%s) > clamp (%s); clamping"):format(tostring(rareRate), tostring(maxClamp)), 1)
        rareRate = maxClamp
    end
    if epicRate > maxClamp then
        log_line(("WARN: GemTweaks_Probability_Epic (%s) > clamp (%s); clamping"):format(tostring(epicRate), tostring(maxClamp)), 1)
        epicRate = maxClamp
    end
    if legendaryRate > maxClamp then
        log_line(("WARN: GemTweaks_Probability_Legendary (%s) > clamp (%s); clamping"):format(tostring(legendaryRate), tostring(maxClamp)), 1)
        legendaryRate = maxClamp
    end

    if type(salvageRate) ~= "number" or salvageRate < minClamp then
        log_line("WARN: GemTweaks_SalvageRate invalid, skipping: " .. tostring(salvageRate), 1)
        feature_end(false)
        return
    end
    if type(commonRate) ~= "number" or commonRate < minClamp then
        log_line("WARN: GemTweaks_Probability_Common invalid, skipping: " .. tostring(commonRate), 1)
        feature_end(false)
        return
    end
    if type(uncommonRate) ~= "number" or uncommonRate < minClamp then
        log_line("WARN: GemTweaks_Probability_Uncommon invalid, skipping: " .. tostring(uncommonRate), 1)
        feature_end(false)
        return
    end
    if type(rareRate) ~= "number" or rareRate < minClamp then
        log_line("WARN: GemTweaks_Probability_Rare invalid, skipping: " .. tostring(rareRate), 1)
        feature_end(false)
        return
    end
    if type(epicRate) ~= "number" or epicRate < minClamp then
        log_line("WARN: GemTweaks_Probability_Epic invalid, skipping: " .. tostring(epicRate), 1)
        feature_end(false)
        return
    end
    if type(legendaryRate) ~= "number" or legendaryRate < minClamp then
        log_line("WARN: GemTweaks_Probability_Legendary invalid, skipping: " .. tostring(legendaryRate), 1)
        feature_end(false)
        return
    end

    local btRes = get_first_resource_by_type("keen::BalancingTable")
    local bt = btRes and btRes.data
    if not bt then
        log_line("WARN: keen::BalancingTable not found; skipping", 1)
        feature_end(false)
        return
    end

    local patchedFields = 0

    if bt.gemCrafting ~= nil then
        if bt.gemCrafting.salvageGainPercentage ~= nil then
            bt.gemCrafting.salvageGainPercentage = salvageRate
            patchedFields = patchedFields + 1
        else
            log_line("WARN: BalancingTable.gemCrafting.salvageGainPercentage missing; skipping field", 1)
        end
    else
        log_line("WARN: BalancingTable.gemCrafting missing; skipping field", 1)
    end

    if bt.gemSlotProbability ~= nil then
        if bt.gemSlotProbability.common ~= nil then
            bt.gemSlotProbability.common = commonRate
            patchedFields = patchedFields + 1
        else
            log_line("WARN: BalancingTable.gemSlotProbability.common missing; skipping field", 1)
        end

        if bt.gemSlotProbability.uncommon ~= nil then
            bt.gemSlotProbability.uncommon = uncommonRate
            patchedFields = patchedFields + 1
        else
            log_line("WARN: BalancingTable.gemSlotProbability.uncommon missing; skipping field", 1)
        end

        if bt.gemSlotProbability.rare ~= nil then
            bt.gemSlotProbability.rare = rareRate
            patchedFields = patchedFields + 1
        else
            log_line("WARN: BalancingTable.gemSlotProbability.rare missing; skipping field", 1)
        end

        if bt.gemSlotProbability.epic ~= nil then
            bt.gemSlotProbability.epic = epicRate
            patchedFields = patchedFields + 1
        else
            log_line("WARN: BalancingTable.gemSlotProbability.epic missing; skipping field", 1)
        end

        if bt.gemSlotProbability.legendary ~= nil then
            bt.gemSlotProbability.legendary = legendaryRate
            patchedFields = patchedFields + 1
        else
            log_line("WARN: BalancingTable.gemSlotProbability.legendary missing; skipping field", 1)
        end
    else
        log_line("WARN: BalancingTable.gemSlotProbability missing; skipping field", 1)
    end

    log_line(("BalancingTable patchedFields=%d salvageRate=%s commonRate=%s uncommonRate=%s rareRate=%s epicRate=%s legendaryRate=%s"):format(
        patchedFields, tostring(salvageRate), tostring(commonRate), tostring(uncommonRate), tostring(rareRate), tostring(epicRate), tostring(legendaryRate)
    ), 1)

    local didWork = (patchedFields > 0)
    feature_end(didWork)
end

return ApplyGemTweaks
