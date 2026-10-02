local UNLOCK_ALL_KNOWLEDGE_ID = 1715248921

local function ApplyCraftingTweaks()
    feature_begin("Crafting Tweaks", 1)

    if not Enable_CraftingTweaks then
        feature_end(false)
        return
    end

    local unlockRecipes = CraftingTweaks_UnlockAllRecipes
    local creativeMode = CraftingTweaks_CreativeMode

    if not unlockRecipes and not creativeMode then
        log_line("No sub-features enabled; skipping.", 1)
        feature_end(false)
        return
    end

    local registryList = game.assets.get_resources_by_type("keen::RecipeRegistryResource")
    if not registryList or #registryList == 0 then
        log_line("WARN: keen::RecipeRegistryResource not found; skipping", 1)
        feature_end(false)
        return
    end

    local recipeCount = 0
    local unlockChanged = 0
    local unlockSkipped = 0
    local unlockFailed = 0
    local creativeChanged = 0
    local creativeSkipped = 0
    local creativeFailed = 0

    local function set_value_wrapper(wrapper, value)
        if wrapper and wrapper.value ~= value then
            wrapper.value = value
            return true
        end

        return false
    end

    local function unlock_recipe_requirement(recipe)
        if not recipe or not recipe.knowledgeRequirement then
            return false
        end

        local requirement = recipe.knowledgeRequirement
        local changed = false

        if not requirement.knowledgeOrQueryId then
            return false
        end

        -- 1715248921 is the current base-started bool knowledge used by older
        -- unlock-all reference mods. The field shape changed, so set the whole
        -- current requirement shape instead of writing obsolete .id fields.
        changed = set_value_wrapper(requirement.knowledgeOrQueryId, UNLOCK_ALL_KNOWLEDGE_ID) or changed

        if requirement.compareValue ~= 1 then
            requirement.compareValue = 1
            changed = true
        end
        if requirement.compareOperator ~= "Equals" then
            requirement.compareOperator = "Equals"
            changed = true
        end
        if requirement.type ~= "SimpleBool" then
            requirement.type = "SimpleBool"
            changed = true
        end
        if requirement.isExplicitPlayerKnowledgeQuery ~= false then
            requirement.isExplicitPlayerKnowledgeQuery = false
            changed = true
        end

        return changed
    end

    local function zero_input_costs(input)
        if input == nil then
            return false
        end

        local changed = false
        for _, entry in ipairs(input) do
            local itemStack = entry and entry.itemStack
            if itemStack and type(itemStack.count) == "number" and itemStack.count ~= 0 then
                itemStack.count = 0
                changed = true
            end

            local inputItemCategory = entry and entry.inputItemCategory
            if inputItemCategory and type(inputItemCategory.count) == "number" and inputItemCategory.count ~= 0 then
                inputItemCategory.count = 0
                changed = true
            end
        end

        return changed
    end

    for _, reg in ipairs(registryList) do
        local data = reg and reg.data
        if data and data.recipes then
            for _, recipe in ipairs(data.recipes) do
                if recipe then
                    recipeCount = recipeCount + 1

                    if unlockRecipes then
                        local success, changed = pcall(function()
                            return unlock_recipe_requirement(recipe)
                        end)

                        if success then
                            if changed then
                                unlockChanged = unlockChanged + 1
                            else
                                unlockSkipped = unlockSkipped + 1
                            end
                        else
                            unlockFailed = unlockFailed + 1
                            if LOG_LEVEL >= 2 then
                                log_line("WARN: Unlock All Recipes failed for recipe: " .. tostring(changed), 2)
                            end
                        end
                    end

                    if creativeMode then
                        local success, changed = pcall(function()
                            return zero_input_costs(recipe.input)
                        end)

                        if success then
                            if changed then
                                creativeChanged = creativeChanged + 1
                            else
                                creativeSkipped = creativeSkipped + 1
                            end
                        else
                            creativeFailed = creativeFailed + 1
                            if LOG_LEVEL >= 2 then
                                log_line("WARN: Creative Mode failed for recipe: " .. tostring(changed), 2)
                            end
                        end
                    end
                end
            end
        end
    end

    if unlockRecipes then
        log_line(("Unlock All Recipes: changed=%d skipped=%d failed=%d total=%d"):format(unlockChanged, unlockSkipped, unlockFailed, recipeCount), 1)
    end
    if creativeMode then
        log_line(("Creative Mode: changed=%d skipped=%d failed=%d total=%d"):format(creativeChanged, creativeSkipped, creativeFailed, recipeCount), 1)
    end

    local didWork = (unlockChanged > 0 or creativeChanged > 0)
    feature_end(didWork)
end

return ApplyCraftingTweaks
