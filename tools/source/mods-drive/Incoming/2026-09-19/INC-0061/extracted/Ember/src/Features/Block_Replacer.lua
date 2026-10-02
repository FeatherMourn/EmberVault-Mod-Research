-- ========================================
--              BLOCK REPLACER
-- ========================================

local function ApplyBlockMaterialReplacer()
    feature_begin("Block Replacement", 1)

    if not Enable_BlockMaterialReplacer then
        feature_end(false)
        return
    end

    local changed = 0
    local skipped = 0
    local lines = {}

    local list = BlockMaterialReplacements
    if type(list) ~= "table" then
        if LOG_LEVEL >= 2 then
            log_line("WARN: BlockMaterialReplacements is not a table; skipping", 2)
        end
        feature_end(false)
        return
    end

    for _, cfg in ipairs(list) do
        local enabled = cfg and cfg.enabled == true
        local materialIndex = cfg and cfg.materialIndex
        local targetGuid = cfg and cfg.targetGuid

        if enabled
            and type(materialIndex) == "number"
            and materialIndex == materialIndex
            and materialIndex ~= math.huge
            and materialIndex ~= -math.huge
            and type(targetGuid) == "string"
            and targetGuid ~= ""
        then
            local okTop, errTop = pcall(function()
                local r = game.assets.get_resource(targetGuid, "keen::ItemInfo", 0)
                if not (r and r.data and r.data.equipment) then
                    table.insert(lines, "SKIP: missing ItemInfo/Equipment for guid=" .. tostring(targetGuid))
                    skipped = skipped + 1
                    return
                end

                local d = r.data
                local eq = d.equipment

                local slotStr = tostring(eq.slot or "")
                local dbgStr = tostring(d.debugName or "")

                table.insert(lines, string.format(
                    "guid=%s slot=%s debugName=%s wantedMaterialIndex=%s",
                    tostring(targetGuid), slotStr, dbgStr, tostring(materialIndex)
                ))

                local looksLikeBlock =
                    (slotStr:find("BlueprintMaterial", 1, true) ~= nil) or
                    (dbgStr:find("Block_", 1, true) == 1)

                if not looksLikeBlock then
                    table.insert(lines, "SKIP: does not match looksLikeBlock gate")
                    skipped = skipped + 1
                    return
                end

                local vd = eq.voxelData
                if not vd then
                    table.insert(lines, "SKIP: eq.voxelData is nil")
                    skipped = skipped + 1
                    return
                end

                local beforeId = vd.placeVoxelMaterialId
                vd.placeVoxelMaterialId = materialIndex
                local afterId = vd.placeVoxelMaterialId

                table.insert(lines, string.format(
                    "voxelData.placeVoxelMaterialId: %s -> %s (wanted %s)",
                    tostring(beforeId), tostring(afterId), tostring(materialIndex)
                ))

                if vd.isBuildingVoxel ~= nil then
                    vd.isBuildingVoxel = true
                end

                changed = changed + 1
            end)

            if not okTop then
                table.insert(lines, "WARN: Block Material Replacer failed for guid=" .. tostring(targetGuid) .. " err=" .. tostring(errTop))
                skipped = skipped + 1
            end
        else
            skipped = skipped + 1
        end
    end

    if LOG_LEVEL >= 2 and #lines > 0 then
        log_block(lines, 2)
    end

    if LOG_LEVEL >= 2 then
        log_line(string.format("summary changed=%d skipped=%d", changed, skipped), 2)
    end

    feature_end(changed > 0)
end

return ApplyBlockMaterialReplacer
