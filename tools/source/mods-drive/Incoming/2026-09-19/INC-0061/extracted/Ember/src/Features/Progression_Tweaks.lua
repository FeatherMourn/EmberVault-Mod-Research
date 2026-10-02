-- ========================================
--          PROGRESSION TWEAKS
-- ========================================

local function get_clamped_skill_points()
    local skillPointsPL = SkillPointsPerLevel

    if type(skillPointsPL) ~= "number" or skillPointsPL < 1 then
        return nil, "WARN: SkillPoints invalid, skipping: " .. tostring(skillPointsPL)
    end

    local maxSkillClamp = SkillPoints_MaxClamp
    if type(maxSkillClamp) == "number" and maxSkillClamp >= 1 then
        if skillPointsPL > maxSkillClamp then
            log_line(("WARN: SkillPoints (%s) > clamp (%s); clamping"):format(tostring(skillPointsPL), tostring(maxSkillClamp)), 1)
            skillPointsPL = maxSkillClamp
        end
    end

    return math.floor(skillPointsPL), nil
end

local function ApplyPlayerItemLevelTweaks()
    feature_begin("Player / Item Level Tweaks", 1)

    if not Enable_PlayerItemLevelTweaks then
        feature_end(false)
        return
    end

    local plevelMax = PlayerLevelMax
    local plevelCap = PlayerLevelCap
    local ilevelCap = ItemLevelCap

    local maxClamp = PlayerItemLevel_MaxClamp
    if type(maxClamp) == "number" and maxClamp >= 1 then
        if plevelMax > maxClamp then
            log_line(("WARN: PlayerLevelMax (%s) > clamp (%s); clamping"):format(tostring(plevelMax), tostring(maxClamp)), 1)
            plevelMax = maxClamp
        end
        if plevelCap > maxClamp then
            log_line(("WARN: PlayerLevelCap (%s) > clamp (%s); clamping"):format(tostring(plevelCap), tostring(maxClamp)), 1)
            plevelCap = maxClamp
        end
        if ilevelCap > maxClamp then
            log_line(("WARN: ItemLevelCap (%s) > clamp (%s); clamping"):format(tostring(ilevelCap), tostring(maxClamp)), 1)
            ilevelCap = maxClamp
        end
    end

    if type(plevelMax) ~= "number" or plevelMax < 1 then
        log_line("WARN: PlayerLevelMax invalid, skipping: " .. tostring(plevelMax), 1)
        feature_end(false)
        return
    end
    if type(plevelCap) ~= "number" or plevelCap < 1 then
        log_line("WARN: PlayerLevelCap invalid, skipping: " .. tostring(plevelCap), 1)
        feature_end(false)
        return
    end
    if type(ilevelCap) ~= "number" or ilevelCap < 1 then
        log_line("WARN: ItemLevelCap invalid, skipping: " .. tostring(ilevelCap), 1)
        feature_end(false)
        return
    end
    if plevelCap > plevelMax then
        log_line(("WARN: PlayerLevelCap (%s) > PlayerLevelMax (%s); clamping cap to max"):format(tostring(plevelCap), tostring(plevelMax)), 1)
        plevelCap = plevelMax
    end

    local btRes = get_first_resource_by_type("keen::BalancingTable")
    local bt = btRes and btRes.data
    if not bt then
        log_line("WARN: keen::BalancingTable not found; skipping", 1)
        feature_end(false)
        return
    end

    local patchedFields = 0

    if bt.playerLevelMax ~= nil then
        bt.playerLevelMax = plevelMax
        patchedFields = patchedFields + 1
    else
        log_line("WARN: BalancingTable.playerLevelMax missing; skipping field", 1)
    end

    if bt.playerLevelCap ~= nil then
        bt.playerLevelCap = plevelCap
        patchedFields = patchedFields + 1
    else
        log_line("WARN: BalancingTable.playerLevelCap missing; skipping field", 1)
    end

    if bt.itemLevelCap ~= nil then
        bt.itemLevelCap = ilevelCap
        patchedFields = patchedFields + 1
    else
        log_line("WARN: BalancingTable.itemLevelCap missing; skipping field", 1)
    end

    log_line(("BalancingTable patchedFields=%d playerLevelMax=%s playerLevelCap=%s itemLevelCap=%s"):format(
        patchedFields, tostring(plevelMax), tostring(plevelCap), tostring(ilevelCap)
    ), 1)

    local syncedItemsChanged = 0
    local didSyncRun = false

    if Enable_ItemLevelCapSync then
        didSyncRun = true

        local skipNeedle = tostring(ItemLevelSync_SafetySkip or "")
        if skipNeedle == "" then
            log_line("WARN: ItemLevelSync_SafetySkip is blank; will not skip any items", 1)
        end

        local items = game.assets.get_resources_by_type("keen::ItemInfo")
        if not items or #items == 0 then
            log_line("WARN: No ItemInfo entries found for maxLevel match", 1)
            feature_end(patchedFields > 0)
            return
        end

        local scanned = 0
        local eligible = 0
        local skipped = 0

        local shown = 0
        local SHOW_LIMIT = 25

        for _, it in ipairs(items) do
            scanned = scanned + 1

            local ok, err = pcall(function()
                local d = it and it.data
                if not d then
                    skipped = skipped + 1
                    return
                end

                local dbg = tostring(d.debugName or "")
                if skipNeedle ~= "" and dbg:find(skipNeedle, 1, true) ~= nil then
                    skipped = skipped + 1
                    return
                end

                local range = d.itemLevelRange
                if not range or type(range) ~= "table" or range.maxLevel == nil then
                    skipped = skipped + 1
                    return
                end

                eligible = eligible + 1

                local before = range.maxLevel
                if type(before) == "number" and before == ilevelCap then
                    return
                end

                range.maxLevel = ilevelCap
                syncedItemsChanged = syncedItemsChanged + 1

                if LOG_LEVEL >= 2 and shown < SHOW_LIMIT then
                    shown = shown + 1
                    log_line(("item[%d] debugName=%s maxLevel: %s -> %s"):format(
                        shown, dbg, tostring(before), tostring(ilevelCap)
                    ), 2)
                end
            end)

            if not ok then
                skipped = skipped + 1
                if LOG_LEVEL >= 2 then
                    log_line("WARN: ItemInfo patch failed guid=" .. tostring(it and it.guid or "nil") .. " err=" .. tostring(err), 2)
                end
            end
        end

        log_line(("ItemLevelCapSync scanned=%d eligible=%d changed=%d skipped=%d (skipIfContains=%s)"):format(
            scanned, eligible, syncedItemsChanged, skipped, tostring(ItemLevelSync_SafetySkip)
        ), 1)

        if LOG_LEVEL >= 2 and syncedItemsChanged > SHOW_LIMIT then
            log_line("(Display list truncated, increase SHOW_LIMIT to print all)", 2)
        end
    else
        log_line("ItemLevelCapSync: disabled", 1)
    end

    local didWork = (patchedFields > 0) or (didSyncRun and syncedItemsChanged > 0)
    feature_end(didWork)
end

local function ApplySkillPointsPerLevel()
    feature_begin("Skill Points Per Level", 1)

    if not (Enable_SkillPointsPerLevel or Enable_PlayerItemLevelTweaks) then
        feature_end(false)
        return
    end

    local skillPointsPL, err = get_clamped_skill_points()
    if err then
        log_line(err, 1)
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

    if bt.skillPointsPerLevel == nil then
        log_line("WARN: BalancingTable.skillPointsPerLevel missing; skipping field", 1)
        feature_end(false)
        return
    end

    local before = bt.skillPointsPerLevel
    bt.skillPointsPerLevel = skillPointsPL

    log_line(("BalancingTable.skillPointsPerLevel: %s -> %s"):format(
        tostring(before), tostring(skillPointsPL)
    ), 1)

    feature_end(true)
end

local function ApplyProgressionTweaks()
    ApplyPlayerItemLevelTweaks()
    ApplySkillPointsPerLevel()
end

return ApplyProgressionTweaks
