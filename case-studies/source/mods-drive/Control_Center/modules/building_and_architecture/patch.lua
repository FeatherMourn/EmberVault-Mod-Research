-- ============================================================================
-- Module: Building, Materials & Architecture (building_and_architecture)
-- Target: keen::BuildingMaterialParametersResource, keen::BalancingTable
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Building & Architecture sliding scale modifications...")

    local discountPct = config.building_cost_discount_pct or 0

    -- 1. Building Material Placement Cost Slider (0% to 100%)
    if discountPct > 0 then
        local matResList = context.GetResources("keen::BuildingMaterialParametersResource")
        if matResList and #matResList > 0 then
            local count = 0
            local factor = 1.0 - (discountPct / 100.0)
            for _, res in ipairs(matResList) do
                local d = res and res.data
                if d and d.materials and type(d.materials) == "table" then
                    for _, mat in ipairs(d.materials) do
                        if mat.costPerBlock and mat.costPerBlock > 1 then
                            if discountPct >= 100 then
                                mat.costPerBlock = 1
                            else
                                mat.costPerBlock = math.max(1, math.floor(mat.costPerBlock * factor))
                            end
                            count = count + 1
                        end
                    end
                end
            end
            context.Log("Discounted block placement costs on " .. tostring(count) .. " building materials by " .. tostring(discountPct) .. "%!")
        end
    end

    -- 2. Flame Altar Territory Radius Slider (1.0x to 5.0x)
    if config.altar_build_radius_mult and config.altar_build_radius_mult > 1.0 then
        local tables = context.GetResources("keen::BalancingTable")
        if tables and #tables > 0 then
            for _, res in ipairs(tables) do
                local d = res and res.data
                if d and d.buildzoneSizesPerAltarLevel and type(d.buildzoneSizesPerAltarLevel) == "table" then
                    for i = 1, #d.buildzoneSizesPerAltarLevel do
                        d.buildzoneSizesPerAltarLevel[i] = math.floor(d.buildzoneSizesPerAltarLevel[i] * config.altar_build_radius_mult)
                    end
                    context.Log("Multiplied build zone sizes per altar level by " .. tostring(config.altar_build_radius_mult))
                end
            end
        end
    end
end

return Module
