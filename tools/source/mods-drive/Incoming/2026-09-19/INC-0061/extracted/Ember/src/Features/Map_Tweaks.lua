-- ========================================
--               MAP TWEAKS
-- ========================================

local function apply_fast_travel_tweaks()
    local toggles = {
        None = FastTravel_None,
        FlameRelated = FastTravel_FlameMarkers,
        Dungeons = FastTravel_DungeonMarkers,
        Locations = FastTravel_LocationMarkers,
        CustomMarker = FastTravel_CustomMarker,
    }

    local registry_res = get_first_resource_by_type("keen::MapMarkerRegistryResource")
    if not registry_res or not registry_res.data then
         log_line("ERROR: MapMarkerRegistryResource not found", 1)
         return false
    end

    local registry = registry_res.data
    local changed = 0
    local matched = 0
    local markers = registry.mapMarkers

    if not markers then
         log_line("ERROR: mapMarkers list missing", 1)
         return false
    end

    local ok, err = pcall(function()
        for i, marker in ipairs(markers) do
             local cat = marker.sortingCategory
             local enabled = toggles[cat]
             if enabled ~= nil then
                 matched = matched + 1
                 if marker.isFastTravelDestination ~= enabled then
                     marker.isFastTravelDestination = enabled
                     changed = changed + 1
                 end
             end
        end
    end)

    if not ok then
        log_line("ERROR in loop: " .. tostring(err), 1)
        return false
    end

    log_line(("Fast Travel markers matched=%d changed=%d"):format(matched, changed), 1)
    return true
end

local function apply_fog_of_war_tweaks()
    local range = FogOfWar_Range
    if type(range) ~= "number" or range <= 0 then
        log_line("WARN: FogOfWar_Range invalid; skipping: " .. tostring(range), 1)
        return false
    end

    local maxClamp = FogOfWar_MaxRangeClamp
    if type(maxClamp) == "number" and maxClamp > 0 and range > maxClamp then
        log_line(("WARN: FogOfWar_Range (%s) > clamp (%s); clamping"):format(tostring(range), tostring(maxClamp)), 1)
        range = maxClamp
    end

    local templates = game.assets.get_resources_by_type("keen::ecs::TemplateResource")
    if not templates or #templates == 0 then
        log_line("WARN: No TemplateResource entries found for Fog of War", 1)
        return false
    end

    local matched = 0
    local changed = 0

    local ok, err = pcall(function()
        for _, res in ipairs(templates) do
            local comps = res and res.data and res.data.components
            if comps then
                for _, comp in ipairs(comps) do
                    if comp and comp.type == "keen::ecs::FogOfWarDiscovery" then
                        matched = matched + 1
                        local v = comp.value
                        if v then
                            if v.discoveryRange ~= range then
                                v.discoveryRange = range
                                changed = changed + 1
                            end
                        end
                    end
                end
            end
        end
    end)

    if not ok then
        log_line("ERROR: Fog of War tweak failed: " .. tostring(err), 1)
        return false
    end

    log_line(("Fog of War discoveryRange matched=%d changed=%d range=%s"):format(
        matched, changed, tostring(range)
    ), 1)

    return true
end

local function ApplyFastTravelTweaks()
    feature_begin("Map Tweaks", 1)

    local didWork = false

    if Enable_FastTravelTweaks then
        didWork = apply_fast_travel_tweaks() or didWork
    end

    if Enable_FogOfWarTweaks then
        didWork = apply_fog_of_war_tweaks() or didWork
    end

    feature_end(didWork)
end

return ApplyFastTravelTweaks
