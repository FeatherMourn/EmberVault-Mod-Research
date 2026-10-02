-- ============================================================================
-- Module: Architect Companion & Free-Cam (architect_companion)
-- Derived from Architect Toolkit & Verified Keen BalancingTable structures
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Initializing Architect Companion Module...")

    local balancingTables = context.GetResources("keen::BalancingTable")
    local bt = (balancingTables and #balancingTables > 0 and balancingTables[1].data) or nil

    if bt then
        -- 1. Flame Altar Build Radius Multiplier
        if config.altar_build_radius_mult and config.altar_build_radius_mult > 1 then
            local sizes = bt.buildzoneSizesPerAltarLevel
            if sizes then
                local changed = 0
                for _, v in ipairs(sizes) do
                    if v.x and v.y and v.z then
                        v.x = math.floor(v.x * config.altar_build_radius_mult)
                        v.y = math.floor(v.y * config.altar_build_radius_mult)
                        v.z = math.floor(v.z * config.altar_build_radius_mult)
                        changed = changed + 1
                    end
                end
                context.Log("Expanded buildzoneSizesPerAltarLevel across " .. tostring(changed) .. " altar levels!")
            end
        end

        -- 2. Max Flame Altars Count Multiplier
        if bt.altarsPerFlameLevel then
            for idx, count in ipairs(bt.altarsPerFlameLevel) do
                bt.altarsPerFlameLevel[idx] = math.min(100, count * 5)
            end
            context.Log("Increased altarsPerFlameLevel cap to 100.")
        end
    else
        context.LogWarn("BalancingTable not found for Architect building tweaks.")
    end
end

function Module.OnLiveConfigUpdate(config, context)
    -- Reserved for live IPC
end

return Module
