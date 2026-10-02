-- ============================================================================
-- Module: Music, Instruments & Campfire Songs (music_and_instruments)
-- Target: keen::SamplerInstrumentResource, keen::BalancingTable
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Music & Instrument modifications...")

    -- 1. Comfort Buff from Instruments in BalancingTable
    if config.instrument_comfort_buff_mult and config.instrument_comfort_buff_mult > 1.0 then
        local tables = context.GetResources("keen::BalancingTable")
        if tables and #tables > 0 then
            for _, res in ipairs(tables) do
                local d = res and res.data
                if d then
                    if d.maximumTotalMusicComfortBuff then
                        d.maximumTotalMusicComfortBuff = math.floor(d.maximumTotalMusicComfortBuff * config.instrument_comfort_buff_mult)
                    end
                end
            end
            context.Log("Scaled maximum instrument comfort buffs in BalancingTable!")
        end
    end

    -- 2. Volume Boost on Instruments
    if config.instrument_volume_boost and config.instrument_volume_boost > 1.0 then
        local instruments = context.GetResources("keen::SamplerInstrumentResource")
        if instruments and #instruments > 0 then
            for _, res in ipairs(instruments) do
                local inst = res and res.data
                if inst and inst.volume then
                    inst.volume = math.min(2.0, inst.volume * config.instrument_volume_boost)
                end
            end
            context.Log("Enhanced acoustic volume for " .. tostring(#instruments) .. " instruments!")
        end
    end
end

return Module
