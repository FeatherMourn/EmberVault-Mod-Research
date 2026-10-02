-- ============================================================================
-- Module: Crafting, Recipes & Workbench Tuning (crafting_and_recipes)
-- Target: keen::RecipeRegistryResource
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Crafting & Recipe sliding scale modifications...")

    local registries = context.GetResources("keen::RecipeRegistryResource")
    if not registries or #registries == 0 then
        context.LogWarn("No keen::RecipeRegistryResource found!")
        return
    end

    local reg = registries[1].data
    if not reg or not reg.recipes then
        context.LogWarn("Recipe list invalid in registry!")
        return
    end

    local speedMult = config.craft_speed_multiplier or 1.0
    local discountPct = config.ingredient_cost_discount_pct or 0
    local yieldMult = config.recipe_yield_multiplier or 1

    local patchedCount = 0
    for _, recipe in ipairs(reg.recipes) do
        -- 1. Crafting Speed Slider (1.0x to 50.0x / Instant)
        if speedMult > 1.0 then
            if recipe.craftTime and recipe.craftTime > 0 then
                if speedMult >= 50.0 then
                    recipe.craftTime = 0.0
                else
                    recipe.craftTime = recipe.craftTime / speedMult
                end
            end
            if recipe.timeNeeded and recipe.timeNeeded > 0 then
                if speedMult >= 50.0 then
                    recipe.timeNeeded = 0.0
                else
                    recipe.timeNeeded = recipe.timeNeeded / speedMult
                end
            end
        end

        -- 2. Ingredient Cost Discount Slider (0% to 100%)
        -- EML exposes some recipe collections as userdata/64-bit keyed views.
        -- Only traverse ordinary Lua tables here; string indexing those views
        -- raises a native type error and can destabilize startup patching.
        if discountPct > 0 and type(recipe) == "table" and recipe.ingredients and type(recipe.ingredients) == "table" then
            local factor = 1.0 - (discountPct / 100.0)
            for _, ing in ipairs(recipe.ingredients) do
                if ing.amount and ing.amount > 1 then
                    if discountPct >= 100 then
                        ing.amount = 1
                    else
                        ing.amount = math.max(1, math.floor(ing.amount * factor))
                    end
                end
                if ing.count and ing.count > 1 then
                    if discountPct >= 100 then
                        ing.count = 1
                    else
                        ing.count = math.max(1, math.floor(ing.count * factor))
                    end
                end
            end
        end

        -- 3. Recipe Output Yield Multiplier (1x to 10x)
        if yieldMult > 1 and type(recipe) == "table" and type(recipe.output) == "table" then
            if recipe.output.amount then
                recipe.output.amount = recipe.output.amount * yieldMult
            end
            if recipe.output.count then
                recipe.output.count = recipe.output.count * yieldMult
            end
        end

        patchedCount = patchedCount + 1
    end

    context.Log("Scaled " .. tostring(patchedCount) .. " recipes (Speed: " .. tostring(speedMult) .. "x, Discount: " .. tostring(discountPct) .. "%, Yield: " .. tostring(yieldMult) .. "x)!")

    -- 4. Injected Master Convenience Recipes
    if config.inject_master_recipes then
        local customRecipes = {
            {
                recipeId = { value = 9988001 },
                output = { itemId = { value = 1300101 }, amount = 1 }, -- Ghost Glider
                ingredients = { { itemId = { value = 722268629 }, amount = 1 } },
                craftTime = 0.0
            },
            {
                recipeId = { value = 9988002 },
                output = { itemId = { value = 1300201 }, amount = 1 }, -- Extraordinary Hook
                ingredients = { { itemId = { value = 722268629 }, amount = 1 } },
                craftTime = 0.0
            },
            {
                recipeId = { value = 9988003 },
                output = { itemId = { value = 3087875 }, amount = 50 }, -- Greater Health Potions
                ingredients = { { itemId = { value = 722268629 }, amount = 1 } },
                craftTime = 0.0
            },
            {
                recipeId = { value = 9988004 },
                output = { itemId = { value = 3087876 }, amount = 50 }, -- Greater Mana Potions
                ingredients = { { itemId = { value = 722268629 }, amount = 1 } },
                craftTime = 0.0
            }
        }

        for _, cr in ipairs(customRecipes) do
            table.insert(reg.recipes, cr)
        end
        context.Log("Injected " .. tostring(#customRecipes) .. " convenience recipes!")
    end
end

return Module
