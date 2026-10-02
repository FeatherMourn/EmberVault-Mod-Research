-- ========================================
--            BUILDING TWEAKS
-- ========================================
local function BuildingTweaks()
    feature_begin("Building Tweaks", 1)
    if not Enable_BuildingTweaks then
        feature_end(false)
        return
    end
    local scenes = game.assets.get_resources_by_type("keen::SceneResource")
    if not scenes or #scenes == 0 then
        log_line("WARN: No SceneResource entries found", 1)
        feature_end(false)
        return
    end
    local TARGET_IBL = "9743d1a0-007d-4a8a-9088-82d34ce7a697"
    log_line("  Target IBL: " .. tostring(TARGET_IBL), 1)
    local sceneChanged = 0
    for _, s in ipairs(scenes) do
        local d = s and s.data
        if d and d.ibl == TARGET_IBL then
            if d.noBuildZones ~= nil then
                d.noBuildZones = {}
                sceneChanged = sceneChanged + 1
            end
        end
    end
    log_line("  SceneResource noBuildZones cleared: " .. tostring(sceneChanged), 1)
    local didWork = (sceneChanged > 0)
    if not Enable_PlacementTweaks then
        log_line("  Placement Tweaks: disabled", 1)
        feature_end(didWork)
        return
    end
    local buildInFog = (PlacementTweaks_BuildInFog == true)
    local noZoneNeed = (PlacementTweaks_NoBuildZoneNeeded == true)
    if not buildInFog and not noZoneNeed then
        log_line("  Placement Tweaks: enabled, but all sub-tweaks are disabled", 1)
        feature_end(didWork)
        return
    end
    local items = game.assets.get_resources_by_type("keen::ItemInfo")
    if not items or #items == 0 then
        log_line("WARN: No ItemInfo entries found for placement-rule edits", 1)
        feature_end(didWork)
        return
    end
    local skipNeedle = tostring(PlacementTweaks_SafetySkip or "")
    if skipNeedle == "" then
        log_line("  Placement Tweaks: no safety-skip string set", 2)
    end
    local scanned = 0
    local eligible = 0
    local skipped = 0
    local failed = 0
    local changedAllowBelowFog = 0
    local changedInhibitBuild = 0
    local changedBuildZoneReq = 0
    local changedInteraction = 0
    local changedPermissions = 0
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
            local eq = d.equipment
            if not eq then
                skipped = skipped + 1
                return
            end
            eligible = eligible + 1
            local changedAny = false
            if buildInFog then
                local ok1 = pcall(function()
                    if eq.allowPlacementBelowFog ~= true then
                        eq.allowPlacementBelowFog = true
                        changedAllowBelowFog = changedAllowBelowFog + 1
                        changedAny = true
                    end
                end)
                local ok2 = pcall(function()
                    local current = tostring(eq.checkInhibitBuild)
                    if current == "Strict" or current == "Lenient" then
                        eq.checkInhibitBuild = "None"
                        changedInhibitBuild = changedInhibitBuild + 1
                        changedAny = true
                    end
                end)
            end
            if noZoneNeed then
                local ok3 = pcall(function()
                    if eq.buildZoneRequired ~= false then
                        eq.buildZoneRequired = false
                        changedBuildZoneReq = changedBuildZoneReq + 1
                        changedAny = true
                    end
                end)
                local ok4 = pcall(function()
                    if d.permissionSetup then
                         if d.permissionSetup.isSet ~= false then
                            d.permissionSetup.isSet = false
                            changedPermissions = changedPermissions + 1
                            changedAny = true
                         end
                    end
                end)
                local ok5 = pcall(function()
                    local entity = eq.placedEntity
                    if entity and entity.components then
                        local comp = find_component_by_type(entity.components, "keen::ecs::DismantleOverride")
                        if comp then
                            if comp.ignoreBuildZoneChecks ~= true then
                                comp.ignoreBuildZoneChecks = true
                                changedInteraction = changedInteraction + 1
                                changedAny = true
                            end
                        else
                            local newComp = {
                                type = "keen::ecs::DismantleOverride",
                                ignoreBuildZoneChecks = true,
                                overrideMethod = false,
                                method = 0,
                                overrideVolumeClass = false,
                                volumeClass = 0,
                                preventDismantlingWithFilledInventory = false
                            }
                            table.insert(entity.components, newComp)
                            changedInteraction = changedInteraction + 1
                            changedAny = true
                        end
                    end
                end)
            end
            if changedAny then
                didWork = true
            end
            if LOG_LEVEL >= 2 and changedAny and shown < SHOW_LIMIT then
                shown = shown + 1
                log_line(("  item[%d] debugName=%s patched"):format(shown, dbg), 2)
            end
        end)
        if not ok then
            failed = failed + 1
            if LOG_LEVEL >= 2 then
                log_line("WARN: ItemInfo placement-rule patch failed guid=" .. tostring(it and it.guid or "nil") .. " err=" .. tostring(err), 2)
            end
        end
    end
    log_line(("  ItemInfo scanned=%d eligible=%d skipped=%d failed=%d"):format(
        scanned, eligible, skipped, failed
    ), 1)
    log_line(("  Patches: Fog=%d | Inhibit=%d | NoZone=%d | Perms=%d | Interaction(Inj)=%d"):format(
        changedAllowBelowFog, changedInhibitBuild, changedBuildZoneReq, changedPermissions, changedInteraction
    ), 1)
    if LOG_LEVEL >= 2 and shown >= SHOW_LIMIT then
        log_line("  (Display list truncated, increase SHOW_LIMIT to print all)", 2)
    end
    feature_end(didWork)
end

return BuildingTweaks
