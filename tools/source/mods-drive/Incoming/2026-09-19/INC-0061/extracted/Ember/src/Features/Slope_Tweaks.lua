-- ========================================
--              SLOPE TWEAKS
-- ========================================
local function SlopeTweaks()
    feature_begin("Slope Tweaks", 1)

    if not Enable_SlopeTweaks then
        feature_end(false)
        return
    end

    log_line(string.format(
        "  steepFloorAngle = %.1f | slidingAngle=%.1f | fallDamageAngle=%.1f",
        steepFloorAngle, slidingAngle, fallDamageAngle
    ), 1)

    local playerRes = game.assets.get_resource(
        "c3db66d6-89a5-4a6c-a8e3-d9a1f6009812",
        "keen::ecs::TemplateResource",
        0
    )

    if not playerRes or not playerRes.data then
        log_line("ERROR: player TemplateResource not found", 1)
        feature_end(false)
        return
    end

    local player = playerRes.data
    local patched = 0

    for _, component in ipairs(player.components or {}) do
        if component.type == "keen::ecs::SlopeConfig" then
            local slope_config = component.value

            local before = {
                steep   = slope_config.slopeDefinition.steepFloorAngle,
                sliding = slope_config.slopeDefinition.slidingAngle,
                fall    = slope_config.slopeDefinition.fallDamageAngle,
            }

            slope_config.slopeDefinition.steepFloorAngle = math.min(steepFloorAngle, Max_Angle)
            slope_config.slopeDefinition.slidingAngle    = math.min(slidingAngle, Max_Angle)
            slope_config.slopeDefinition.fallDamageAngle = math.min(fallDamageAngle, Max_Angle)

            patched = patched + 1

            if LOG_LEVEL >= 2 then
                log_line(string.format("  component[%d]", patched), 2)
                log_line(string.format("    steepFloorAngle: %.1f -> %.1f", before.steep, slope_config.slopeDefinition.steepFloorAngle), 2)
                log_line(string.format("    slidingAngle:    %.1f -> %.1f", before.sliding, slope_config.slopeDefinition.slidingAngle), 2)
                log_line(string.format("    fallDamageAngle: %.1f -> %.1f", before.fall, slope_config.slopeDefinition.fallDamageAngle), 2)
            end
        end
    end

    feature_end(patched > 0)
end

return SlopeTweaks
