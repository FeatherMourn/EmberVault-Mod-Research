-- ========================================
--               FOG TWEAKS
-- ========================================
local function ApplyFogTweaks()
    feature_begin("Fog Tweaks", 1)

    if not Enable_FogTweaks then
        feature_end(false)
        return
    end

    local res = get_first_resource_by_type("keen::VolumetricFog3Resource")
    if not res or not res.data then
        log_line("WARN: keen::VolumetricFog3Resource missing; skipping.", 1)
        feature_end(false)
        return
    end

    local data = res.data
    local mats = data.materials
    if not mats then
        log_line("WARN: VolumetricFog3Resource.data.materials missing; skipping.", 1)
        feature_end(false)
        return
    end

    local changed_count = 0

    local function validate(val, clamp)
        if type(val) ~= "number" then return nil end
        if val > clamp then return clamp end
        if val < 0 then return 0 end
        return val
    end

    local function apply(target_tbl, field_name, new_val, log_name)
        if new_val == nil then return end
        if target_tbl[field_name] ~= new_val then
            if LOG_LEVEL >= 2 then
                log_line(("%s: %s -> %s"):format(log_name, tostring(target_tbl[field_name]), tostring(new_val)), 2)
            end
            target_tbl[field_name] = new_val
            changed_count = changed_count + 1
        end
    end

    local function apply_material(index, density_cfg, opacity_cfg)
        local mat = mats[index]
        if not mat then return end

        local d = validate(density_cfg, Fog_Density_MaxClamp)
        local o = validate(opacity_cfg, Fog_Opacity_MaxClamp)

        apply(mat, "densityScale", d, ("Mat[%d].Density"):format(index))
        apply(mat, "extinction", o, ("Mat[%d].Opacity"):format(index))
    end

    local function apply_barrier_mat(target_tbl, name_prefix, emissiveExp_cfg, emissive_cfg, opacity_cfg, scatter_cfg)
        if not target_tbl then return end

        local ee = validate(emissiveExp_cfg, Fog_Emissive_MaxClamp)
        local e  = validate(emissive_cfg,    Fog_Emissive_MaxClamp)
        local o  = validate(opacity_cfg,     Fog_Opacity_MaxClamp)
        local s  = validate(scatter_cfg,     Fog_Scatter_MaxClamp)

        apply(target_tbl, "emissiveExposuredIntensity", ee, name_prefix .. ".EmissiveExposed")
        apply(target_tbl, "emissiveIntensity",          e,  name_prefix .. ".Emissive")
        apply(target_tbl, "extinction",                 o,  name_prefix .. ".Opacity")
        apply(target_tbl, "scatterBoost",               s,  name_prefix .. ".ScatterBoost")
    end

    local ok, err = pcall(function()
        apply_material(1, Fog_M1_Density, Fog_M1_Opacity)
        apply_material(2, Shroud_Fog_Dangerous_Density, Shroud_Fog_Dangerous_Opacity)
        apply_material(3, Shroud_Fog_Deadly_Density, Shroud_Fog_Deadly_Opacity)

        apply(data, "rainExtinction",     validate(Rain_Opacity, Fog_Opacity_MaxClamp),     "RainOpacity")
        apply(data, "snowExtinction",     validate(Snow_Opacity, Fog_Opacity_MaxClamp),     "SnowOpacity")
        apply(data, "blizzardExtinction", validate(Blizzard_Opacity, Fog_Opacity_MaxClamp), "BlizzardOpacity")

        if data.heightFogMaterial then
            local hfd = validate(HeightFog_Density, Fog_Density_MaxClamp)
            local hfo = validate(HeightFog_Opacity, Fog_Opacity_MaxClamp)
            apply(data.heightFogMaterial, "densityScale", hfd, "HeightFog.Density")
            apply(data.heightFogMaterial, "extinction",   hfo, "HeightFog.Opacity")
        end

        apply(data, "barrierFogThickness", validate(Ambient_Fog_Density, Fog_Density_MaxClamp), "BarrierThickness")

        apply_barrier_mat(data.dangerousBarrierFogMaterial, "DangerousBarrier",
            Dangerous_Fog_Barrier_Exposed_Emissive_Intensity,
            Dangerous_Fog_Barrier_Emissive_Intensity,
            Dangerous_Fog_Barrier_Opacity,
            Dangerous_Fog_Barrier_Scatter_Boost
        )

        apply_barrier_mat(data.deadlyBarrierFogMaterial, "DeadlyBarrier",
            Deadly_Fog_Barrier_Exposed_Emissive_Intensity,
            Deadly_Fog_Barrier_Emissive_Intensity,
            Deadly_Fog_Barrier_Opacity,
            Deadly_Fog_Barrier_Scatter_Boost
        )

    end)

    if not ok then
        log_line("ERROR applying fog tweaks: " .. tostring(err), 1)
        feature_end(false)
        return
    end

    log_line(("Applied changes to %d fields."):format(changed_count), 1)
    feature_end(changed_count > 0)
end

return ApplyFogTweaks
