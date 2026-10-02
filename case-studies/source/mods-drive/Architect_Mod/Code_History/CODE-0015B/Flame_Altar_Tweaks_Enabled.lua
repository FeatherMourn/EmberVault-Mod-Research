-- ==================================================
--              Flame Altar Tweaks
-- ==================================================
-- User-tuned defaults (2026-09-17)
-- Force this feature on and raise the number of Flame Altars allowed per Flame level.
-- Current tuning: 5x vanilla counts, with a hard cap of 100.
Enable_FlameAltarTweaks = true
MaxFlameAltars_Multiplier = 5
MaxFlameAltars_Cap = 100

-- Safety clamp for future tuning. This does not reduce the current 5x setting.
FlameAltar_MaxMultiplierClamp = 20

local function ApplyFlameAltarTweaks()
    feature_begin("Flame Altar Tweaks", 1)

    if not Enable_FlameAltarTweaks then
        feature_end(false)
        return
    end

    local mult = MaxFlameAltars_Multiplier
    local cap  = MaxFlameAltars_Cap

    if type(mult) ~= "number" or mult <= 0 then
        log_line("WARN: MaxFlameAltars_Multiplier invalid; skipping: " .. tostring(mult), 1)
        feature_end(false)
        return
    end
    if type(cap) ~= "number" or cap < 1 then
        log_line("WARN: MaxFlameAltars_Cap invalid; skipping: " .. tostring(cap), 1)
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

    local altarLevels = bt.altarsPerFlameLevel
    if not altarLevels then
        log_line("WARN: BalancingTable.altarsPerFlameLevel missing; skipping", 1)
        feature_end(false)
        return
    end

    local vanillaMax = 0
    for _, v in ipairs(altarLevels) do
        if type(v) == "number" and v > vanillaMax then
            vanillaMax = v
        end
    end

    local clampMult = FlameAltar_MaxMultiplierClamp
    if type(clampMult) == "number" and clampMult > 0 and vanillaMax > 0 then
        if mult > clampMult then
            log_line(("WARN: MaxFlameAltars_Multiplier (%s) > clamp (%s); clamping"):format(tostring(mult), tostring(clampMult)), 1)
            mult = clampMult
        end

        local maxAllowedCap = math.floor((vanillaMax * clampMult) + 0.5)
        if cap > maxAllowedCap then
            log_line(("WARN: MaxFlameAltars_Cap (%s) > clamp (%s = vanillaMax(%s)*%s); clamping"):format(
                tostring(cap), tostring(maxAllowedCap), tostring(vanillaMax), tostring(clampMult)
            ), 1)
            cap = maxAllowedCap
        end
    end

    local scanned = 0
    local changed = 0
    local skipped = 0
    local failed  = 0

    local shown = 0
    local SHOW_LIMIT = 25

    for i, oldCount in ipairs(altarLevels) do
        scanned = scanned + 1

        local ok, err = pcall(function()
            if type(oldCount) ~= "number" then
                skipped = skipped + 1
                return
            end

            local rawNew = oldCount * mult
            local newCount = math.floor(rawNew + 0.5)

            if newCount > cap then newCount = cap end

            if newCount > oldCount then
                altarLevels[i] = newCount
                changed = changed + 1

                if LOG_LEVEL >= 2 and shown < SHOW_LIMIT then
                    shown = shown + 1
                    log_line(("  flameLevel[%d] altars: %s -> %s (raw=%s cap=%s)"):format(
                        i, tostring(oldCount), tostring(newCount), tostring(rawNew), tostring(cap)
                    ), 2)
                end
            else
                skipped = skipped + 1
            end
        end)

        if not ok then
            failed = failed + 1
            if LOG_LEVEL >= 2 then
                log_line("WARN: altarsPerFlameLevel patch failed idx=" .. tostring(i) .. " err=" .. tostring(err), 2)
            end
        end
    end

    log_line(("  altarsPerFlameLevel scanned=%d changed=%d skipped=%d failed=%d multiplier=%s cap=%s"):format(
        scanned, changed, skipped, failed, tostring(mult), tostring(cap)
    ), 1)

    if LOG_LEVEL >= 2 and changed > SHOW_LIMIT then
        log_line("  (Display list truncated, increase SHOW_LIMIT to print all)", 2)
    end

    feature_end(changed > 0)
end

return ApplyFlameAltarTweaks
