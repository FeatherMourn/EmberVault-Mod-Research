-- ========================================
--       TERRAIN MATERIAL REPLACER
-- ========================================
local function is_blank_guid(g)
    return g == nil or g == "" or g == "00000000-0000-0000-0000-000000000000"
end

local function ApplyVoxelMaterialReplacer()
    feature_begin("Terrain Replacement", 1)

    if not Enable_VoxelMaterialReplacer then
        feature_end(false)
        return
    end

    local changed = 0
    local shown = 0
    local SHOW_LIMIT = 30

    for _, cfg in ipairs(VoxelMaterialReplacements or {}) do
        if cfg.enabled and cfg.toId ~= nil and not is_blank_guid(cfg.targetGuid) then
            local r = game.assets.get_resource(cfg.targetGuid, "keen::ItemInfo", 0)
            if r and r.data and r.data.equipment and r.data.equipment.voxelData then
                local slotStr = tostring(r.data.equipment.slot or "")
                if slotStr == "TerrainMaterial" then
                    r.data.equipment.voxelData.isBuildingVoxel = false
                end

                local before = r.data.equipment.voxelData.placeVoxelMaterialId
                r.data.equipment.voxelData.placeVoxelMaterialId = cfg.toId
                local after = r.data.equipment.voxelData.placeVoxelMaterialId

                changed = changed + 1

                if LOG_LEVEL >= 2 and shown < SHOW_LIMIT then
                    shown = shown + 1
                    log_line(string.format(
                        "guid=%s materialId: %s -> %s (wanted %s)",
                        tostring(cfg.targetGuid),
                        tostring(before),
                        tostring(after),
                        tostring(cfg.toId)
                    ), 2)
                end
            end
        end
    end

    if LOG_LEVEL >= 2 and changed > SHOW_LIMIT then
        log_line("(Display list truncated, increase SHOW_LIMIT to print all)", 2)
    end

    feature_end(changed > 0)
end

return ApplyVoxelMaterialReplacer
