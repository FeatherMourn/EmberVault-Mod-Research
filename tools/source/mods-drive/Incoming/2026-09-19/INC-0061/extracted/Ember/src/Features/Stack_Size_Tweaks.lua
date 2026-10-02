-- ========================================
--           STACK SIZE TWEAKS
-- ========================================
local function ApplyStackSizeTweaks()
    feature_begin("Stack Size Tweaks", 1)

    if not Enable_StackSizeTweaks then
        feature_end(false)
        return
    end

    local maxStack = StackSize_MaxStack

    if type(maxStack) == "number" and maxStack > 65535 then
        log_line("WARN: StackSize_MaxStack " .. tostring(maxStack) .. " exceeds 65535. Clamping to 65535.", 1)
        maxStack = 65535
    end

    if type(maxStack) ~= "number" or maxStack < 1 then
        feature_end(false)
        return
    end

    local items = game.assets.get_resources_by_type("keen::ItemInfo")
    if not items or #items == 0 then
        feature_end(false)
        return
    end

    local changed = 0

    for _, it in ipairs(items) do
        local d = it and it.data
        local cur = d and d.maxStackSize
        if type(cur) == "number" and cur > 1 and cur ~= maxStack then
            local ok = pcall(function()
                d.maxStackSize = maxStack
            end)
            if ok then
                changed = changed + 1
            end
        end
    end

    if changed > 0 then
        log_line((" Max Stack Size ➡ %s"):format(tostring(maxStack)), 1)
    end

    feature_end(changed > 0)
end

return ApplyStackSizeTweaks
