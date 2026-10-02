-- ============================================================================
-- Module: Buffs, Potions & Status Effects (buffs_and_status)
-- Target: keen::BuffType
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Buff & Status Effect modifications...")

    local buffList = context.GetResources("keen::BuffType")
    if not buffList or #buffList == 0 then
        context.LogWarn("No keen::BuffType resources found!")
        return
    end

    local modifiedCount = 0
    for _, res in ipairs(buffList) do
        local b = res and res.data
        if b then
            -- 1. Buff Lifetime Multiplier
            if config.buff_lifetime_multiplier and config.buff_lifetime_multiplier > 1.0 then
                if b.defaultLifeTime and b.defaultLifeTime.value and b.defaultLifeTime.value > 0 then
                    b.defaultLifeTime.value = math.floor(b.defaultLifeTime.value * config.buff_lifetime_multiplier)
                    modifiedCount = modifiedCount + 1
                end
            end

            -- 2. Persist on Death
            if config.persist_buffs_through_death then
                b.despawnOnDeath = false
            end

            -- 3. Food Poisoning Immunity
            if config.mitigate_food_poisoning and b.isFoodPoison then
                b.isFoodPoison = false
                if b.defaultLifeTime and b.defaultLifeTime.value then
                    b.defaultLifeTime.value = 100000 -- 0.1s
                end
            end
        end
    end

    context.Log("Patched " .. tostring(modifiedCount) .. " buff definitions!")
end

return Module
