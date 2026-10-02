-- ============================================================================
-- Module: Inventory, Items & Equipment Overhaul (inventory_and_items)
-- Target: keen::ItemInfo
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Item & Equipment sliding scale modifications...")

    local items = context.GetResources("keen::ItemInfo")
    if not items or #items == 0 then
        context.LogWarn("No keen::ItemInfo resources found!")
        return
    end

    local stackMult = config.max_stack_multiplier or 1
    local durMult = config.durability_multiplier or 1.0
    local dmgMult = config.weapon_damage_multiplier or 1.0

    local stackChanged = 0
    local gearChanged = 0

    for _, res in ipairs(items) do
        local item = res and res.data
        if item then
            -- 1. Stack Size Multiplier Slider
            if stackMult > 1 then
                if item.maxStackSize and item.maxStackSize > 1 then
                    item.maxStackSize = math.min(65535, math.floor(item.maxStackSize * stackMult))
                    stackChanged = stackChanged + 1
                end
            end

            -- 2. Equipment Modifications
            if item.equipment then
                local eq = item.equipment

                -- Durability Multiplier Slider (1.0x to 50.0x / Infinite)
                if durMult > 1.0 then
                    if eq.durability and eq.durability > 0 then
                        if durMult >= 50.0 then
                            eq.durability = 99999
                        else
                            eq.durability = math.floor(eq.durability * durMult)
                        end
                        gearChanged = gearChanged + 1
                    end
                end

                -- Damage Multiplier Slider
                if dmgMult > 1.0 then
                    if item.damageSetup then
                        local ds = item.damageSetup
                        if ds.damageValues and type(ds.damageValues) == "table" then
                            for _, dv in ipairs(ds.damageValues) do
                                if dv.damage then
                                    dv.damage = dv.damage * dmgMult
                                end
                            end
                        end
                    end
                end
            end
        end
    end

    context.Log("Updated stack sizes on " .. tostring(stackChanged) .. " items and scaled durability/damage on " .. tostring(gearChanged) .. " gear items!")
end

return Module
