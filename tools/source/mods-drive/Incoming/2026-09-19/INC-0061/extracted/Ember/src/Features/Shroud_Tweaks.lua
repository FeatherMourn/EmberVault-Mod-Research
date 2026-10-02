-- ========================================
--         SHROUD TIMER TWEAKS
-- ========================================
local function ApplyShroudTimerTweaks()
    feature_begin("Shroud Timer Tweaks", 1)

    if not Enable_ShroudTimerTweaks then
        feature_end(false)
        return
    end

    local multiplier = ShroudTimer_Multiplier
    if type(multiplier) == "number" and multiplier > ShroudTimer_MaxMultiplierClamp then
        log_line("WARN: ShroudTimer_Multiplier " .. tostring(multiplier) .. " exceeds clamp. Clamping to " .. tostring(ShroudTimer_MaxMultiplierClamp), 1)
        multiplier = ShroudTimer_MaxMultiplierClamp
    end

    if type(multiplier) ~= "number" or multiplier <= 0 then
         log_line("Invalid multiplier. Skipping.", 1)
         feature_end(false)
         return
    end

    local TARGET_GUID = "82706b40-61b1-4b8f-8b23-dcec6971bda1"
    local tables = game.assets.get_resources_by_type("keen::BalancingTable")
    local applied = false

    for _, res in ipairs(tables or {}) do
        if tostring(res.guid) == TARGET_GUID then
            local ok, err = pcall(function()
                local base = res.data.playerBaseFogResistance
                local new_val = base * multiplier

                res.data.playerBaseFogResistance = new_val

                log_line(("Applied %sx Multiplier to playerBaseFogResistance"):format(tostring(multiplier)), 1)
                log_line(("Base Time: %s -> %s"):format(tostring(base), tostring(new_val)), 2)
                applied = true
            end)

            if not ok then
                log_line("Error applying Shroud Timer Tweaks: " .. tostring(err), 1)
            end
            break
        end
    end

    if not applied then
         log_line("Target BalancingTable not found.", 2)
    end

    feature_end(applied)
end

return ApplyShroudTimerTweaks
