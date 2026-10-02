-- ========================================
--          EA BARRIER REMOVAL
-- ========================================
local function NoBarriers()
    feature_begin("No Barriers", 1)

    if not Enable_NoBarriers then
        feature_end(false)
        return
    end

    local SCENE_GUIDS = {
        "36234b22-85f2-4001-ac56-002b379d0d88",
        "509feadb-4c60-425f-9c7c-deeefd9b6920",
        "6e616060-71df-4a67-903e-fe6b8319c58f",
        "892172f0-1bf5-4fb4-af3a-6b05b624b39f",
        "987bd339-f334-4902-812f-b0e29d7d393d"
    }

    log_line("  Scenes to patch: " .. tostring(#SCENE_GUIDS), 1)

    local patched = 0
    local idx = 0
    for _, guid in ipairs(SCENE_GUIDS) do
        idx = idx + 1

        local scene = game.assets.get_resource(guid, "keen::SceneResource", 0)
        if scene and scene.data then
            local bounds = scene.data.resetPlayersOutOfBounds
            if bounds and bounds.playableAreas then
                bounds.playableAreas = {}
                patched = patched + 1

                if LOG_LEVEL >= 2 then
                    log_line(string.format("  patched[%d]: %s", idx, guid), 2)
                end
            else
                if LOG_LEVEL >= 2 then
                    log_line(string.format("  skip[%d]: %s (no playableAreas)", idx, guid), 2)
                end
            end
        else
            if LOG_LEVEL >= 2 then
                log_line(string.format("  skip[%d]: %s (SceneResource missing)", idx, guid), 2)
            end
        end
    end

    feature_end(patched > 0)
end

return NoBarriers
