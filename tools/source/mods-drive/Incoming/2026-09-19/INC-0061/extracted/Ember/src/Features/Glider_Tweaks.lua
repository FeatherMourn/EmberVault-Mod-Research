-- ========================================
--             GLIDER TUNING
-- ========================================
local GLIDER_GUIDS = {
    ["33834394-99c5-47b2-93b2-36aa6a2eaa73"] = "T1",
    ["1da8d177-3a28-43b1-b430-44b38022d925"] = "T2",
    ["f5520401-f5aa-41cd-99e1-609b884cc492"] = "T3",
    ["80c9eaeb-7fa0-480d-a55f-91c2c51b383e"] = "T4_REWARD",
}

local GLIDER_NAMES = {
    ["Tool_Glider_T1"]        = "T1",
    ["Tool_Glider_T2"]        = "T2",
    ["Tool_Glider_T3"]        = "T3",
    ["Tool_Glider_T4_REWARD"] = "T4_REWARD",
}

local GLIDER_FIELDS = {
    "accelerationForward",
    "airResistanceLongitudinal",
    "airResistanceLateral",
    "airResistanceVertical",
    "yawAngleSpeed",
    "pitchAngleSpeed",
    "rollAngleSpeed",
}

local function ApplyGliderTuning()
    feature_begin("Glider Stats", 1)

    if not Enable_GliderTuning then
        feature_end(false)
        return
    end

    local items = game.assets.get_resources_by_type("keen::ItemInfo")
    if not items then
        log_line("ERROR: get_resources_by_type('keen::ItemInfo') returned nil", 1)
        feature_end(false)
        return
    end

    local totalCount = #items
    log_line("Total ItemInfo resources: " .. tostring(totalCount), 1)

    local glidersFound = 0
    local glidersModified = 0

    local function fmt(v, decimals)
        if type(v) ~= "number" then return tostring(v) end
        decimals = decimals or 2
        return string.format("%." .. tostring(decimals) .. "f", v)
    end

    for idx = 1, totalCount do
        local res = items[idx]
        if not res then goto continue end

        local ok, err = pcall(function()
            local d = res.data
            if not d then return end

            local eq = d.equipment
            if not eq then return end

            local slotStr = tostring(eq.slot)
            if slotStr ~= "Glider" then return end

            glidersFound = glidersFound + 1

            local guid = tostring(res.guid or "unknown")
            local debugName = tostring(d.debugName or "unknown")

            local tier = GLIDER_GUIDS[guid] or GLIDER_NAMES[debugName]
            if not tier then
                log_line("WARNING: Unknown glider found - guid=" .. guid .. " debugName=" .. debugName, 2)
                return
            end

            local tierConfig = GliderConfig[tier]
            if not tierConfig then
                log_line("WARNING: No config for tier " .. tostring(tier), 2)
                return
            end

            local gc = eq.gliderConfig
            if not gc then
                log_line("WARNING: gliderConfig is nil for " .. debugName, 2)
                return
            end

            log_line(string.format("- Glider - %s", tier), 1)

            local changedAny = false

            for _, field in ipairs(GLIDER_FIELDS) do
                local override = tierConfig[field]
                if override ~= nil then
                    local before = gc[field]
                    gc[field] = override
                    local after = gc[field]

                    local dec = (field:find("AngleSpeed", 1, true) ~= nil) and 1 or 2

                    log_line(string.format(
                        "  %s: %s -> %s",
                        field,
                        fmt(before, dec),
                        fmt(after,  dec)
                    ), 1)

                    changedAny = true
                end
            end

            if changedAny then
                glidersModified = glidersModified + 1
            else
                log_line("Glider " .. tier .. " (" .. debugName .. ") - no overrides configured", 2)
            end
        end)

        if not ok then
            log_line("WARN: Glider patch failed for resource index=" .. tostring(idx) .. " err=" .. tostring(err), 1)
        end

        ::continue::
    end

    feature_end(glidersModified > 0)
end

return ApplyGliderTuning
