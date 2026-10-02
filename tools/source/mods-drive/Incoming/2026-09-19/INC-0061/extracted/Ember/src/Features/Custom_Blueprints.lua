-- ==================================================
--               Blueprint Injector
-- ==================================================
local function ApplyBlueprintInjector()
    feature_begin("Blueprint Injector", 1)

    if not Enable_BlueprintInjector then
        feature_end(false)
        return
    end

    local newId = BlueprintInjector_NewItemId
    local newName = BlueprintInjector_NewDebugName

    local sx, sy, sz = BlueprintInjector_SizeX, BlueprintInjector_SizeY, BlueprintInjector_SizeZ
    local scale = BlueprintInjector_VoxelsToMeters

    if type(newId) ~= "number" or newId < 1 then
        log_line("WARN: BlueprintInjector_NewItemId invalid; skipping: " .. tostring(newId), 1)
        feature_end(false)
        return
    end
    if type(newName) ~= "string" or newName == "" then
        log_line("WARN: BlueprintInjector_NewDebugName invalid; skipping: " .. tostring(newName), 1)
        feature_end(false)
        return
    end
    if type(sx) ~= "number" or type(sy) ~= "number" or type(sz) ~= "number" or sx < 1 or sy < 1 or sz < 1 then
        log_line(("WARN: Blueprint size invalid; skipping: x=%s y=%s z=%s"):format(tostring(sx), tostring(sy), tostring(sz)), 1)
        feature_end(false)
        return
    end
    sx, sy, sz = math.floor(sx + 0.5), math.floor(sy + 0.5), math.floor(sz + 0.5)

    local maxVol = BlueprintInjector_MaxVolume
    local vol = sx * sy * sz
    if type(maxVol) == "number" and maxVol >= 1 and vol > maxVol then
        log_line(("WARN: Blueprint volume too large (%s > %s). Clamp triggered; skipping injector. (x=%d y=%d z=%d)"):format(
            tostring(vol), tostring(maxVol), sx, sy, sz
        ), 1)
        feature_end(false)
        return
    end

    if type(scale) ~= "number" or scale <= 0 then
        log_line("WARN: BlueprintInjector_VoxelsToMeters invalid; skipping: " .. tostring(scale), 1)
        feature_end(false)
        return
    end

    local function generate_voxel_data(x, y, z)
        local total = x * y * z
        if type(total) ~= "number" or total < 1 then return {} end
        total = math.floor(total + 0.5)

        local data = {}
        for i = 1, total do data[i] = 255 end
        return data
    end

    local NEW_SIZE = { x = sx, y = sy, z = sz }
    local NEW_VOXELS = generate_voxel_data(sx, sy, sz)

    local models = game.assets.get_resources_by_type("keen::VoxelModelResource")
    if not models or #models == 0 then
        log_line("WARN: No keen::VoxelModelResource entries found; skipping (expected on server).", 1)
        feature_end(false)
        return
    end

    local reverted = 0
    local revertGuid = tostring(BlueprintInjector_MasterHologramGuid or "")
    if revertGuid ~= "" then
        for _, res in ipairs(models) do
            local g = tostring(res and res.guid or "")
            if g == revertGuid then
                local ok = pcall(function()
                    if res.data and res.data.size and res.data.data then
                        res.data.size = { x = BlueprintInjector_RevertSizeX, y = BlueprintInjector_RevertSizeY, z = BlueprintInjector_RevertSizeZ }

                        local total = (BlueprintInjector_RevertSizeX or 0) * (BlueprintInjector_RevertSizeY or 0) * (BlueprintInjector_RevertSizeZ or 0)
                        total = (type(total) == "number" and total > 0) and math.floor(total + 0.5) or 64

                        local fill = BlueprintInjector_RevertFillValue
                        if type(fill) ~= "number" then fill = 255 end

                        local d = {}
                        for i = 1, total do d[i] = fill end
                        res.data.data = d

                        reverted = reverted + 1
                    end
                end)

                if not ok then
                    log_line("WARN: Revert master hologram failed guid=" .. g, 1)
                end
                break
            end
        end
    end

    local templatePrefix = tostring(BlueprintInjector_TemplateGuidPrefix or "")
    local templateRes = nil
    if templatePrefix == "" then
        log_line("WARN: BlueprintInjector_TemplateGuidPrefix is blank; cannot clone template model.", 1)
    else
        for _, res in ipairs(models) do
            local g = tostring(res and res.guid or "")
            if g ~= "" and g:sub(1, #templatePrefix) == templatePrefix then
                templateRes = res
                break
            end
        end
    end

    if not templateRes or not templateRes.data then
        log_line("WARN: Template voxel model not found; skipping injection (prefix=" .. tostring(templatePrefix) .. ")", 1)
        log_line(("Summary: revertedMaster=%d cloned=0 injectedRegistry=0 injectedItem=0"):format(reverted), 1)
        feature_end(reverted > 0)
        return
    end

    local clonedGuid = nil
    local clonedOk, clonedRes = pcall(function()
        return game.assets.create_resource(templateRes.data, "keen::VoxelModelResource")
    end)

    if clonedOk and clonedRes then
        local patchOk = pcall(function()
            if clonedRes.data then
                clonedRes.data.size = NEW_SIZE
                clonedRes.data.data = NEW_VOXELS
            end
        end)

        if patchOk then
            clonedGuid = clonedRes.guid
        else
            log_line("WARN: Failed to patch cloned voxel model data.", 1)
        end
    else
        log_line("WARN: Failed to clone template VoxelModelResource.", 1)
    end

    if not clonedGuid then
        log_line(("Summary: revertedMaster=%d cloned=0 injectedRegistry=0 injectedItem=0"):format(reverted), 1)
        feature_end(reverted > 0)
        return
    end

    local injectedRegistry = 0
    local injectedItem = 0

    local voxelReg = get_first_resource_by_type("keen::VoxelBlueprintItemRegistryResource")
    local voxelData = voxelReg and voxelReg.data
    local blueprintItems = voxelData and voxelData.blueprintItems

    if not blueprintItems then
        log_line("WARN: keen::VoxelBlueprintItemRegistryResource.blueprintItems not found; skipping registry injection (expected on server).", 1)
    else
        local exists = false
        for _, item in ipairs(blueprintItems) do
            local idv = item and item.itemId and item.itemId.value
            if type(idv) == "number" and idv == newId then
                exists = true
                break
            end
        end

        if not exists then
            local entry = { itemId = { value = newId }, size = NEW_SIZE, data = NEW_VOXELS, isDataCompressed = false }
            local ok = pcall(function() table.insert(blueprintItems, entry) end)
            if ok then injectedRegistry = 1 else log_line("WARN: Failed to insert into VoxelBlueprintItemRegistryResource.blueprintItems", 1) end
        end
    end

    local itemReg = get_first_resource_by_type("keen::ItemRegistryResource")
    local itemRegData = itemReg and itemReg.data
    if not (itemRegData and itemRegData.itemRefs) then
        log_line("WARN: keen::ItemRegistryResource.itemRefs not found; skipping item registration (expected on server).", 1)
        log_line(("Summary: revertedMaster=%d cloned=1 injectedRegistry=%d injectedItem=0 newId=%s newName=%s cloneGuid=%s"):format(
            reverted, injectedRegistry, tostring(newId), tostring(newName), tostring(clonedGuid)
        ), 1)
        feature_end((reverted > 0) or (injectedRegistry == 1))
        return
    end

    local items = game.assets.get_resources_by_type("keen::ItemInfo")
    if not items or #items == 0 then
        log_line("WARN: No keen::ItemInfo resources found; skipping item injection.", 1)
        log_line(("Summary: revertedMaster=%d cloned=1 injectedRegistry=%d injectedItem=0 newId=%s newName=%s cloneGuid=%s"):format(
            reverted, injectedRegistry, tostring(newId), tostring(newName), tostring(clonedGuid)
        ), 1)
        feature_end((reverted > 0) or (injectedRegistry == 1))
        return
    end

    local baseName = tostring(BlueprintInjector_BaseBlueprintDebugName or "")
    if baseName == "" then
        log_line("WARN: BlueprintInjector_BaseBlueprintDebugName is blank; skipping item injection.", 1)
        log_line(("Summary: revertedMaster=%d cloned=1 injectedRegistry=%d injectedItem=0 newId=%s newName=%s cloneGuid=%s"):format(
            reverted, injectedRegistry, tostring(newId), tostring(newName), tostring(clonedGuid)
        ), 1)
        feature_end((reverted > 0) or (injectedRegistry == 1))
        return
    end

    local templateItem = nil
    for _, res in ipairs(items) do
        local d = res and res.data
        if d and d.debugName == baseName then
            templateItem = res
            break
        end
    end

    if not templateItem or not templateItem.data then
        log_line("WARN: ItemInfo template not found for debugName=" .. tostring(baseName), 1)
        log_line(("Summary: revertedMaster=%d cloned=1 injectedRegistry=%d injectedItem=0 newId=%s newName=%s cloneGuid=%s"):format(
            reverted, injectedRegistry, tostring(newId), tostring(newName), tostring(clonedGuid)
        ), 1)
        feature_end((reverted > 0) or (injectedRegistry == 1))
        return
    end

    local createdOk, newItem = pcall(function()
        return game.assets.create_resource(templateItem.data, "keen::ItemInfo")
    end)

    if not (createdOk and newItem and newItem.data) then
        log_line("WARN: Failed to create new ItemInfo from template.", 1)
        log_line(("Summary: revertedMaster=%d cloned=1 injectedRegistry=%d injectedItem=0 newId=%s newName=%s cloneGuid=%s"):format(
            reverted, injectedRegistry, tostring(newId), tostring(newName), tostring(clonedGuid)
        ), 1)
        feature_end((reverted > 0) or (injectedRegistry == 1))
        return
    end

    local itemPatchOk, itemPatchErr = pcall(function()
        if LOG_LEVEL >= 2 then log_line("DEBUG: Starting item patch...", 2) end
        newItem.data.itemId = newItem.data.itemId or {}
        newItem.data.itemId.value = newId
        newItem.data.debugName = newName

        local eq = newItem.data.equipment
        if LOG_LEVEL >= 2 then log_line("DEBUG: equipment type is " .. type(eq), 2) end

        if eq then
            eq.voxelObject = clonedGuid

            local min_x, min_y, min_z = 0, 0, 0
            local max_x = sx * scale
            local max_y = sy * scale
            local max_z = sz * scale


            local half_x = max_x / 2
            local half_z = max_z / 2

            if eq.placementAABBmin and eq.placementAABBmax then
                eq.placementAABBmin.x = 0;     eq.placementAABBmin.y = min_y; eq.placementAABBmin.z = 0
                eq.placementAABBmax.x = max_x; eq.placementAABBmax.y = max_y; eq.placementAABBmax.z = max_z
            end

            if eq.snappingAABBmin and eq.snappingAABBmax then
                eq.snappingAABBmin.x = 0;     eq.snappingAABBmin.y = min_y; eq.snappingAABBmin.z = 0
                eq.snappingAABBmax.x = max_x; eq.snappingAABBmax.y = max_y; eq.snappingAABBmax.z = max_z
            end

            if LOG_LEVEL >= 2 then
                log_line("DEBUG: Checking equipment...", 2)
            end

            local snap = eq.voxelSnappingConfig
            if LOG_LEVEL >= 2 then
                log_line("DEBUG: voxelSnappingConfig is " .. tostring(snap), 2)
            end

            if snap then
                 if LOG_LEVEL >= 2 then
                     log_line("DEBUG: snapBoxOffsetMin is " .. tostring(snap.snapBoxOffsetMin), 2)
                 end
            end

            if snap and snap.snapBoxOffsetMin and snap.snapBoxOffsetMax then

                local off_x = math.floor((sx / 2) - 1)
                if off_x < 0 then off_x = 0 end

                local off_z = math.floor((sz / 2) - 1)
                if off_z < 0 then off_z = 0 end

                local off_y = 0

                snap.snapBoxOffsetMin.x = off_x; snap.snapBoxOffsetMax.x = off_x
                snap.snapBoxOffsetMin.y = off_y; snap.snapBoxOffsetMax.y = off_y
                snap.snapBoxOffsetMin.z = off_z; snap.snapBoxOffsetMax.z = off_z

                if LOG_LEVEL >= 2 then
                    log_line(("DEBUG: Size={%d, %d, %d} Offsets={x=%d, y=%d, z=%d}"):format(sx, sy, sz, off_x, off_y, off_z), 2)
                    log_line(("DEBUG: PlacementAABB: Min={%.2f, %.2f, %.2f} Max={%.2f, %.2f, %.2f}"):format(
                        eq.placementAABBmin.x, eq.placementAABBmin.y, eq.placementAABBmin.z,
                        eq.placementAABBmax.x, eq.placementAABBmax.y, eq.placementAABBmax.z
                    ), 2)
                end
            end
        end
    end)

    if not itemPatchOk then
        log_line("WARN: Failed to patch new ItemInfo fields; skipping registration. err=" .. tostring(itemPatchErr), 1)
        log_line(("Summary: revertedMaster=%d cloned=1 injectedRegistry=%d injectedItem=0 newId=%s newName=%s cloneGuid=%s"):format(
            reverted, injectedRegistry, tostring(newId), tostring(newName), tostring(clonedGuid)
        ), 1)
        feature_end((reverted > 0) or (injectedRegistry == 1))
        return
    end

    local regOk = pcall(function()
        table.insert(itemRegData.itemRefs, newItem.guid)
    end)

    if regOk then
        injectedItem = 1
    else
        log_line("WARN: Failed to register new ItemInfo guid into ItemRegistryResource.itemRefs", 1)
    end

    if LOG_LEVEL >= 2 then
        log_line(("New blueprint: id=%s debugName=%s size={x=%s y=%s z=%s} cloneGuid=%s"):format(
            tostring(newId), tostring(newName), tostring(sx), tostring(sy), tostring(sz), tostring(clonedGuid)
        ), 2)
    end

    log_line(("Summary: revertedMaster=%d cloned=1 injectedRegistry=%d injectedItem=%d newId=%s newName=%s"):format(
        reverted, injectedRegistry, injectedItem, tostring(newId), tostring(newName)
    ), 1)

    local didWork = (reverted > 0) or (injectedRegistry == 1) or (injectedItem == 1)
    feature_end(didWork)
end

return ApplyBlueprintInjector
