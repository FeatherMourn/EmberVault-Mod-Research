-- ========================================
--          Base Size Multipliers
-- ========================================
local function ApplyBaseSizeTweaks()
    feature_begin("Base Size Multipliers", 1)

    if not Enable_BaseSizeTweaks then
        feature_end(false)
        return
    end

    local mult = BaseSize_Multiplier
    if type(mult) ~= "number" or mult <= 0 then
        log_line("WARN: BaseSize_Multiplier invalid; skipping: " .. tostring(mult), 1)
        feature_end(false)
        return
    end

    local maxMult = BaseSize_MaxMultiplierClamp
    if type(maxMult) == "number" and maxMult > 0 and mult > maxMult then
        log_line(("WARN: BaseSize_Multiplier (%s) > clamp (%s); clamping"):format(tostring(mult), tostring(maxMult)), 1)
        mult = maxMult
    end

    local btRes = get_first_resource_by_type("keen::BalancingTable")
    local bt = btRes and btRes.data
    if not bt then
        log_line("WARN: keen::BalancingTable not found; skipping", 1)
        feature_end(false)
        return
    end

    local sizes = bt.buildzoneSizesPerAltarLevel
    if not sizes then
        log_line("WARN: BalancingTable.buildzoneSizesPerAltarLevel missing; skipping", 1)
        feature_end(false)
        return
    end

    local scanned = 0
    local eligible = 0
    local changed = 0
    local skipped = 0
    local failed = 0

    local shown = 0
    local SHOW_LIMIT = 25

    for idx, v in ipairs(sizes) do
        scanned = scanned + 1

        local ok, err = pcall(function()
            local x, y, z = v.x, v.y, v.z
            if type(x) ~= "number" or type(y) ~= "number" or type(z) ~= "number" then
                skipped = skipped + 1
                return
            end

            if x <= 0 then
                skipped = skipped + 1
                return
            end

            eligible = eligible + 1

            local beforeX, beforeY, beforeZ = x, y, z

            local function round_nearest(n) return math.floor(n + 0.5) end
            local newX = round_nearest(x * mult)
            local newY = round_nearest(y * mult)
            local newZ = round_nearest(z * mult)

            if math.abs(newX - x) > 0.01 or math.abs(newY - y) > 0.01 or math.abs(newZ - z) > 0.01 then
                v.x = newX
                v.y = newY
                v.z = newZ
                changed = changed + 1

                if LOG_LEVEL >= 2 and shown < SHOW_LIMIT then
                    shown = shown + 1
                    log_line(string.format(
                        "  entry[%s] (x,y,z): (%.2f, %.2f, %.2f) -> (%.2f, %.2f, %.2f)",
                        tostring(idx),
                        beforeX, beforeY, beforeZ,
                        v.x, v.y, v.z
                    ), 2)
                end
            else
                skipped = skipped + 1
            end
        end)

        if not ok then
            failed = failed + 1
            if LOG_LEVEL >= 2 then
                log_line("WARN: buildzoneSizesPerAltarLevel patch failed idx=" .. tostring(idx) .. " err=" .. tostring(err), 2)
            end
        end
    end

    log_line(("  buildzoneSizesPerAltarLevel scanned=%d eligible=%d changed=%d skipped=%d failed=%d multiplier=%s"):format(
        scanned, eligible, changed, skipped, failed, tostring(mult)
    ), 1)

    if LOG_LEVEL >= 2 and shown >= SHOW_LIMIT then
        log_line("  (Display list truncated, increase SHOW_LIMIT to print all)", 2)
    end

    feature_end(changed > 0)
end

return ApplyBaseSizeTweaks
