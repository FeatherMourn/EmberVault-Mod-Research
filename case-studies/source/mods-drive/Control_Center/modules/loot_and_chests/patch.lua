-- ============================================================================
-- Module: Loot Tables, Chests & Drop Rates (loot_and_chests)
-- Target: keen::LootableItemsResource, keen::fishing::TrashLootTableResource
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Loot Table & Drop Rate sliding scale modifications...")

    local lootBoost = config.legendary_drop_rate_boost or 1.0
    local trashRatePct = config.trash_fishing_probability_pct

    -- 1. Lootable Items Rarity Drop Rates Slider (1.0x to 10.0x)
    if lootBoost > 1.0 then
        local lootList = context.GetResources("keen::LootableItemsResource")
        if lootList and #lootList > 0 then
            for _, res in ipairs(lootList) do
                local lt = res and res.data
                if lt and lt.globalRarityDropRates then
                    for k, rate in pairs(lt.globalRarityDropRates) do
                        if type(rate) == "number" then
                            lt.globalRarityDropRates[k] = math.min(1.0, rate * lootBoost)
                        end
                    end
                end
            end
            context.Log("Boosted global rarity drop rates by " .. tostring(lootBoost) .. "x!")
        end
    end

    -- 2. Trash Fishing Probability Slider (0% to 100%)
    if trashRatePct ~= nil and trashRatePct < 100 then
        local trashTables = context.GetResources("keen::fishing::TrashLootTableResource")
        if trashTables and #trashTables > 0 then
            local factor = trashRatePct / 100.0
            for _, res in ipairs(trashTables) do
                local tt = res and res.data
                if tt and tt.entries and type(tt.entries) == "table" then
                    for _, entry in ipairs(tt.entries) do
                        if entry.weight then
                            entry.weight = entry.weight * factor
                        end
                    end
                end
            end
            context.Log("Scaled trash fishing weights to " .. tostring(trashRatePct) .. "%!")
        end
    end
end

return Module
