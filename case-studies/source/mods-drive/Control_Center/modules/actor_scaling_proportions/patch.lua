-- ============================================================================
-- Module: Actor Scaling, Height & Proportions (actor_scaling_proportions)
-- Target: keen::anim_graph::RetargetDataResource, keen::RootMotionScaleConfig
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Actor Scaling & Proportion modifications...")

    local heightScale = config.player_height_scale or 1.0
    local headScale = config.player_head_scale or 1.0
    local strideScale = config.player_stride_scale or 1.0

    -- 1. Bone Retargeting Scale (RetargetDataResource)
    local retargetList = context.GetResources("keen::anim_graph::RetargetDataResource")
    if retargetList and #retargetList > 0 then
        local modifiedCount = 0
        for _, res in ipairs(retargetList) do
            local d = res and res.data
            if d and d.entries and type(d.entries) == "table" then
                for _, entry in ipairs(d.entries) do
                    -- Bone 0 = Root/Pelvis (Overall scale)
                    -- Bone 12/30 = Head / Neck
                    if heightScale ~= 1.0 and (entry.boneIndex == 0 or entry.boneIndex == 6) then
                        entry.uniformScale = entry.uniformScale * heightScale
                        modifiedCount = modifiedCount + 1
                    end
                    if headScale ~= 1.0 and (entry.boneIndex == 12 or entry.boneIndex == 30) then
                        entry.uniformScale = entry.uniformScale * headScale
                        modifiedCount = modifiedCount + 1
                    end
                end
            end
        end
        context.Log("Scaled skeletal proportions across " .. tostring(modifiedCount) .. " bone retarget nodes!")
    end

    -- 2. Root Motion Locomotion Stride Scale (RootMotionScaleConfig)
    if strideScale ~= 1.0 or heightScale ~= 1.0 then
        local effectiveStride = (strideScale ~= 1.0) and strideScale or heightScale
        local rootConfigs = context.GetResources("keen::RootMotionScaleConfig")
        if rootConfigs and #rootConfigs > 0 then
            for _, res in ipairs(rootConfigs) do
                local d = res and res.data
                if d then
                    d.enabled = true
                    if d.scaleMod then
                        d.scaleMod = d.scaleMod * effectiveStride
                    end
                end
            end
            context.Log("Locomotion stride scaled to " .. tostring(effectiveStride) .. "x!")
        end
    end
end

return Module
