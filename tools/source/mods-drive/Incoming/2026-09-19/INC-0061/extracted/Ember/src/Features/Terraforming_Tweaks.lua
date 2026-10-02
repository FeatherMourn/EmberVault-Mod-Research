-- ========================================
--          TERRAFORMING TWEAKS
-- ========================================
local function ApplyTerraformingTweaks()
    feature_begin("Terraforming Tweaks", 1)

    if not Enable_TerraformingTweaks then
        feature_end(false)
        return
    end

    local reg = get_first_resource_by_type("keen::TerraformingEfficiencyRegistryResource")
    local data = reg and reg.data
    local cfgs = data and data.terrainConfigs
    if not cfgs then
        log_line("WARN: TerraformingEfficiencyRegistryResource.terrainConfigs not found", 1)
        feature_end(false)
        return
    end

    local byId = {}
    for _, c in ipairs(cfgs) do
        local id = c.terrainMaterial and c.terrainMaterial.value
        if type(id) == "number" then
            byId[id] = c
        end
    end

    local applied = 0
    local skipped = 0
    local matched = 0
    local missing = 0
    local invalid = 0

    local function invalid_patch_field(p)
        if p.hardness ~= nil and type(p.hardness) ~= "string" then
            return "hardness"
        end
        if p.healthPoints ~= nil and type(p.healthPoints) ~= "number" then
            return "healthPoints"
        end
        if p.damageSusceptibility ~= nil and type(p.damageSusceptibility) ~= "string" then
            return "damageSusceptibility"
        end
        return nil
    end

    for _, p in ipairs(TerraformingTweaks or {}) do
        if p.enabled then
            if type(p.materialId) ~= "number" then
                skipped = skipped + 1
                invalid = invalid + 1
                log_line("WARN: TerraformingTweaks row has invalid materialId: " .. tostring(p.materialId), 1)
            else
                local target = byId[p.materialId]
                local invalidField = invalid_patch_field(p)

                if not target then
                    skipped = skipped + 1
                    missing = missing + 1
                    log_line("WARN: TerraformingTweaks materialId not found in terrainConfigs: " .. tostring(p.materialId), 1)
                elseif invalidField then
                    skipped = skipped + 1
                    invalid = invalid + 1
                    log_line("WARN: TerraformingTweaks materialId=" .. tostring(p.materialId) .. " has invalid " .. invalidField .. "; skipped", 1)
                else
                    matched = matched + 1
                    local changedAny = false

                    if p.hardness ~= nil then
                        if target.hardness ~= p.hardness then
                            target.hardness = p.hardness
                            changedAny = true
                        end
                    end

                    if p.healthPoints ~= nil then
                        if target.healthPoints ~= p.healthPoints then
                            target.healthPoints = p.healthPoints
                            changedAny = true
                        end
                    end

                    if p.damageSusceptibility ~= nil then
                        if target.damageSusceptibility ~= p.damageSusceptibility then
                            target.damageSusceptibility = p.damageSusceptibility
                            changedAny = true
                        end
                    end

                    if changedAny then
                        applied = applied + 1
                        if LOG_LEVEL >= 2 then
                            log_line(
                                "  patched materialId=" .. tostring(p.materialId) ..
                                (p.hardness ~= nil and (" hardness=" .. tostring(p.hardness)) or "") ..
                                (p.healthPoints ~= nil and (" hp=" .. tostring(p.healthPoints)) or "") ..
                                (p.damageSusceptibility ~= nil and (" susceptibility=" .. tostring(p.damageSusceptibility)) or ""),
                                2
                            )
                        end
                    else
                        skipped = skipped + 1
                    end
                end
            end
        end
    end

    log_line(("  matched=%d applied=%d skipped=%d missing=%d invalid=%d"):format(matched, applied, skipped, missing, invalid), 1)

    feature_end(applied > 0)
end


-- Terrain Loot Tweaks
local function ApplyTerrainDropTweaks()
    feature_begin("Terrain Loot Tweaks", 1)

    if not Enable_TerrainDropTweaks then
        feature_end(false)
        return
    end

    local reg = get_first_resource_by_type("keen::TerraformingEfficiencyRegistryResource")
    local data = reg and reg.data
    local cfgs = data and data.terrainConfigs

    if not cfgs then
        log_line("WARN: TerraformingEfficiencyRegistryResource.terrainConfigs not found", 1)
        feature_end(false)
        return
    end

    local rate = TerrainDrop_ExchangeRate
    if type(rate) ~= "number" or rate <= 0 then
        log_line("WARN: TerrainDrop_ExchangeRate invalid, skipping: " .. tostring(rate), 1)
        feature_end(false)
        return
    end

    local changedRate = 0
    for _, c in ipairs(cfgs) do
        if c.terrainPerLootItemExchangeRate ~= nil then
            c.terrainPerLootItemExchangeRate = rate
            changedRate = changedRate + 1
        end
    end

    log_line(("Patched terrainPerLootItemExchangeRate on %d entries (rate=%s)"):format(changedRate, tostring(rate)), 1)
    feature_end(changedRate > 0)
end

local function ApplyTerraformingAndDropTweaks()
    ApplyTerraformingTweaks()
    ApplyTerrainDropTweaks()
end

return ApplyTerraformingAndDropTweaks
