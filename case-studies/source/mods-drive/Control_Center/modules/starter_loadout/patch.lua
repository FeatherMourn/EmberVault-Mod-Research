-- ============================================================================
-- Module: Custom Starter Loadouts & Kits (starter_loadout)
-- Target: keen::DefaultInventoryResource, keen::ds::ecs::DefaultInventoryResource
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    if not config.enable_starter_boost then
        return
    end

    context.Log("Injecting Custom Starter Loadouts into DefaultInventory...")

    local invResources = context.GetResources("keen::DefaultInventoryResource")
    if not invResources or #invResources == 0 then
        invResources = context.GetResources("keen::ds::ecs::DefaultInventoryResource")
    end

    if not invResources or #invResources == 0 then
        context.LogWarn("DefaultInventoryResource not found in KFC cache!")
        return
    end

    for _, res in ipairs(invResources) do
        local d = res and res.data
        if d and d.rootGroup and d.rootGroup.stacks then
            local stacks = d.rootGroup.stacks

            -- 1. Glider & Hook
            if config.include_glider_hook then
                table.insert(stacks, { item = { value = 1300101 }, count = 1 }) -- Ghost Glider
                table.insert(stacks, { item = { value = 1300201 }, count = 1 }) -- Extraordinary Hook
            end

            -- 2. Potions
            if config.starting_potion_count and config.starting_potion_count > 0 then
                table.insert(stacks, { item = { value = 3087875 }, count = config.starting_potion_count }) -- Greater Health
                table.insert(stacks, { item = { value = 3087876 }, count = config.starting_potion_count }) -- Greater Mana
            end

            -- 3. Runes
            if config.starting_runes and config.starting_runes > 0 then
                table.insert(stacks, { item = { value = 1400201 }, count = config.starting_runes }) -- Runes
            end

            context.Log("Injected starter items into DefaultInventory (GUID: " .. tostring(res.guid) .. ")")
        end
    end
end

return Module
