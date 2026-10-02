-- ========================================
--              LOOT TWEAKS
-- ========================================

local function ApplyLootTweaks()
    feature_begin("Loot Tweaks", 1)

    if not Enable_LootTweaks then
        feature_end(false)
        return
    end

    local resMulti = Loot_ResourceDropMultiplier
    local itemMulti = Loot_ItemDropMultiplier
    local maxStack = Loot_MaxStackSize

    if type(resMulti) ~= "number" or resMulti <= 0 then
        log_line("WARN: Loot_ResourceDropMultiplier invalid; skipping: " .. tostring(resMulti), 1)
        feature_end(false)
        return
    end
    if type(itemMulti) ~= "number" or itemMulti <= 0 then
        log_line("WARN: Loot_ItemDropMultiplier invalid; skipping: " .. tostring(itemMulti), 1)
        feature_end(false)
        return
    end

    local maxDropClamp = Loot_DropMultiplierMaxClamp
    if type(maxDropClamp) == "number" and maxDropClamp > 0 then
        if resMulti > maxDropClamp then
            log_line(("WARN: Loot_ResourceDropMultiplier (%s) > clamp (%s); clamping"):format(
                tostring(resMulti), tostring(maxDropClamp)
            ), 1)
            resMulti = maxDropClamp
        end
        if itemMulti > maxDropClamp then
            log_line(("WARN: Loot_ItemDropMultiplier (%s) > clamp (%s); clamping"):format(
                tostring(itemMulti), tostring(maxDropClamp)
            ), 1)
            itemMulti = maxDropClamp
        end
    end

    local maxStackClamp = Loot_MaxStackSizeClamp
    if type(maxStack) == "number" and maxStack >= 1 then
        if type(maxStackClamp) == "number" and maxStackClamp > 0 and maxStack > maxStackClamp then
            log_line(("WARN: Loot_MaxStackSize (%s) > clamp (%s); clamping"):format(
                tostring(maxStack), tostring(maxStackClamp)
            ), 1)
            maxStack = maxStackClamp
        end
    else
        log_line("WARN: Loot_MaxStackSize invalid; stackSizeMaxScaled will not be set", 1)
        maxStack = nil
    end

    local function scale_field(obj, field, mult)
        if not obj or type(obj[field]) ~= "number" then return false end
        local before = obj[field]
        local after = math.floor(before * mult + 0.5)
        if after ~= before then
            obj[field] = after
            return true
        end
        return false
    end

    local items = game.assets.get_resources_by_type("keen::ItemInfo")
    if not items or #items == 0 then
        log_line("WARN: No ItemInfo entries found; skipping", 1)
        feature_end(false)
        return
    end

    local stackables = {}
    for _, it in ipairs(items) do
        local d = it and it.data
        if d and type(d.maxStackSize) == "number" and d.maxStackSize > 1 then
            local id = d.itemId and d.itemId.value
            if type(id) == "number" then
                stackables[id] = true
            end
        end
    end

    local didWork = false

    local defaultInv = game.assets.get_resources_by_type("keen::ecs::DefaultInventoryResource")
    if not defaultInv or #defaultInv == 0 then
        log_line("WARN: No DefaultInventoryResource entries found", 1)
    else
        local scanned = 0
        local changed = 0
        local failed = 0

        for _, res in ipairs(defaultInv) do
            local ok, err = pcall(function()
                local data = res and res.data
                if not data then return end
                for _, group in pairs(data) do
                    local stacks = group and group.stacks
                    if stacks then
                        for _, stack in pairs(stacks) do
                            scanned = scanned + 1
                            local any = false
                            any = scale_field(stack, "countMin", resMulti) or any
                            any = scale_field(stack, "countMax", resMulti) or any
                            if any then changed = changed + 1 end
                        end
                    end
                end
            end)

            if not ok then
                failed = failed + 1
                if LOG_LEVEL >= 2 then
                    log_line("WARN: DefaultInventoryResource pickup patch failed guid=" .. tostring(res and res.guid or "nil") .. " err=" .. tostring(err), 2)
                end
            end
        end

        log_line(("DefaultInventoryResource pickups scanned=%d changed=%d failed=%d mult=%s"):format(
            scanned, changed, failed, tostring(resMulti)
        ), 1)

        if changed > 0 then didWork = true end
    end

    local itemScanned = 0
    local itemChanged = 0
    local itemFailed = 0

    for _, it in ipairs(items) do
        local ok, err = pcall(function()
            local d = it and it.data
            if not d or type(d.maxStackSize) ~= "number" or d.maxStackSize <= 1 then
                return
            end

            local range = d.randomLootStackRange
            if not range then return end

            itemScanned = itemScanned + 1
            local any = false
            any = scale_field(range, "minStackSize", itemMulti) or any
            any = scale_field(range, "maxStackSize", itemMulti) or any
            if any then itemChanged = itemChanged + 1 end
        end)

        if not ok then
            itemFailed = itemFailed + 1
            if LOG_LEVEL >= 2 then
                log_line("WARN: ItemInfo randomLootStackRange patch failed guid=" .. tostring(it and it.guid or "nil") .. " err=" .. tostring(err), 2)
            end
        end
    end

    log_line(("ItemInfo randomLootStackRange scanned=%d changed=%d failed=%d mult=%s"):format(
        itemScanned, itemChanged, itemFailed, tostring(itemMulti)
    ), 1)

    if itemChanged > 0 then didWork = true end

    local lootRes = game.assets.get_resources_by_type("keen::LootableItemsResource")
    if not lootRes or #lootRes == 0 then
        log_line("WARN: No LootableItemsResource entries found", 1)
    else
        local lootScanned = 0
        local lootChanged = 0
        local lootFailed = 0

        for _, res in ipairs(lootRes) do
            local ok, err = pcall(function()
                local data = res and res.data
                local entries = data and data.items
                if not entries then return end

                for _, entry in pairs(entries) do
                    local id = entry and entry.itemId and entry.itemId.value
                    if id and stackables[id] then
                        lootScanned = lootScanned + 1
                        local any = false
                        any = scale_field(entry, "stackSizeMin", itemMulti) or any
                        any = scale_field(entry, "stackSizeMax", itemMulti) or any
                        if entry.stackSizeScalable ~= false then
                            entry.stackSizeScalable = false
                            any = true
                        end
                        if maxStack ~= nil then
                            if entry.stackSizeMaxScaled ~= maxStack then
                                entry.stackSizeMaxScaled = maxStack
                                any = true
                            end
                        end
                        if any then lootChanged = lootChanged + 1 end
                    end
                end
            end)

            if not ok then
                lootFailed = lootFailed + 1
                if LOG_LEVEL >= 2 then
                    log_line("WARN: LootableItemsResource patch failed guid=" .. tostring(res and res.guid or "nil") .. " err=" .. tostring(err), 2)
                end
            end
        end

        log_line(("LootableItemsResource scanned=%d changed=%d failed=%d mult=%s maxStack=%s"):format(
            lootScanned, lootChanged, lootFailed, tostring(itemMulti), tostring(maxStack)
        ), 1)

        if lootChanged > 0 then didWork = true end
    end

    if defaultInv and #defaultInv > 0 then
        local invScanned = 0
        local invChanged = 0
        local invFailed = 0

        local function patch_stacks(stacks)
            if not stacks then return end
            for _, stack in pairs(stacks) do
                local id = stack and stack.item and stack.item.value
                if id and stackables[id] then
                    invScanned = invScanned + 1
                    local any = false
                    any = scale_field(stack, "countMin", itemMulti) or any
                    any = scale_field(stack, "countMax", itemMulti) or any
                    if any then invChanged = invChanged + 1 end
                end
            end
        end

        for _, res in ipairs(defaultInv) do
            local ok, err = pcall(function()
                local root = res and res.data and res.data.rootGroup
                if not root then return end

                patch_stacks(root.stacks)
                for _, group in pairs(root.groups or {}) do
                    patch_stacks(group and group.stacks)
                end
            end)

            if not ok then
                invFailed = invFailed + 1
                if LOG_LEVEL >= 2 then
                    log_line("WARN: DefaultInventoryResource rootGroup patch failed guid=" .. tostring(res and res.guid or "nil") .. " err=" .. tostring(err), 2)
                end
            end
        end

        log_line(("DefaultInventoryResource rootGroup scanned=%d changed=%d failed=%d mult=%s"):format(
            invScanned, invChanged, invFailed, tostring(itemMulti)
        ), 1)

        if invChanged > 0 then didWork = true end
    end

    feature_end(didWork)
end

return ApplyLootTweaks
