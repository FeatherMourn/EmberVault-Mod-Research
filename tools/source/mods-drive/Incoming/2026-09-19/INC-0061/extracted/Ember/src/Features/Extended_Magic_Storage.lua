-- ========================================
--          EXTENDED MAGIC STORAGE
-- ========================================
local MAGIC_STORAGE_TEMPLATE_NAME = "Prop_Decoration_T1_Storage_24_Magic"
local SUPPORTED_MAGIC_COMPONENT_TYPES = {
    "keen::ecs::InventoryCraftingStock",
}

local REQUIRED_TARGET_COMPONENT_TYPE = "keen::ecs::InventorySetup"

local function component_type(component)
    if not component then
        return nil
    end

    return component.type or component["$type"]
end

local function find_component_by_exact_type(components, typeName)
    if not components then
        return nil
    end

    for _, component in ipairs(components) do
        if component_type(component) == typeName then
            return component
        end
    end

    return nil
end

local function deep_copy(value, seen)
    if type(value) ~= "table" then
        return value
    end

    seen = seen or {}
    if seen[value] then
        return seen[value]
    end

    local copy = {}
    seen[value] = copy

    for k, v in pairs(value) do
        copy[deep_copy(k, seen)] = deep_copy(v, seen)
    end

    return copy
end

local function find_template_by_name(templates, templateName)
    for _, t in ipairs(templates) do
        local td = t and t.data
        local name = td and td.name

        if name and string.find(name, templateName, 1, true) then
            return td
        end
    end

    return nil
end

local function get_templates()
    local templates = game.assets.get_resources_by_type("keen::ecs::TemplateResource")
    if not templates or #templates == 0 then
        log_line("WARN: No TemplateResource entries found", 1)
        return nil
    end

    log_line("  TemplateResource count: " .. tostring(#templates), 1)
    return templates
end

local function get_supported_magic_component(templates)
    local magicTemplate = find_template_by_name(templates, MAGIC_STORAGE_TEMPLATE_NAME)

    if not magicTemplate then
        log_line("WARN: Magic storage template not found (" .. MAGIC_STORAGE_TEMPLATE_NAME .. ")", 1)
        return nil, nil
    end

    log_line("  Magic template found: " .. tostring(magicTemplate.name or "nil"), 1)

    for _, typeName in ipairs(SUPPORTED_MAGIC_COMPONENT_TYPES) do
        local component = find_component_by_exact_type(magicTemplate.components, typeName)
        if component then
            log_line("  Magic component type: " .. tostring(typeName), 1)
            return component, typeName
        end
    end

    log_line("WARN: Magic storage source component not found (" .. table.concat(SUPPORTED_MAGIC_COMPONENT_TYPES, ", ") .. "); no templates patched.", 1)
    return nil, nil
end

local function patch_magic_storage_targets(featureName, enabled, targetPredicate, showLimit)
    feature_begin(featureName, 1)

    if not enabled then
        feature_end(false)
        return
    end

    local templates = get_templates()
    if not templates then
        feature_end(false)
        return
    end

    local magicComponent, magicComponentType = get_supported_magic_component(templates)
    if not magicComponent then
        feature_end(false)
        return
    end

    local modified = 0
    local skippedExisting = 0
    local skippedNoInventory = 0
    local shown = 0

    for _, t in ipairs(templates) do
        local td = t and t.data
        local name = td and td.name

        if name and targetPredicate(name) then
            td.components = td.components or {}

            local hasInventorySetup = find_component_by_exact_type(td.components, REQUIRED_TARGET_COMPONENT_TYPE) ~= nil
            if not hasInventorySetup then
                skippedNoInventory = skippedNoInventory + 1
            else
                local already = find_component_by_exact_type(td.components, magicComponentType) ~= nil

                if already then
                    skippedExisting = skippedExisting + 1
                else
                    table.insert(td.components, deep_copy(magicComponent))
                    modified = modified + 1

                    if LOG_LEVEL >= 2 and shown < showLimit then
                        shown = shown + 1
                        log_line("  patched: " .. tostring(name), 2)
                    end
                end
            end
        end
    end

    log_line("  Modified templates: " .. tostring(modified), 1)
    log_line("  Already had component: " .. tostring(skippedExisting), 1)
    log_line("  Skipped without inventory setup: " .. tostring(skippedNoInventory), 1)

    if LOG_LEVEL >= 2 and modified > showLimit then
        log_line("  (Display list truncated, increase showLimit to print all)", 2)
    end

    feature_end(modified > 0)
end

local function is_magic_furniture_target(name)
    return string.find(name, "Prop_Decoration_", 1, true)
        and string.find(name, "Storage", 1, true)
        and not string.find(name, "Magic", 1, true)
        and not string.find(name, "Loot", 1, true)
        and not string.find(name, "DEPRECATED", 1, true)
end

local function is_magic_factory_target(name)
    return string.find(name, "Factory", 1, true)
end

-- Magic Furniture
local function MagicFurniture()
    patch_magic_storage_targets("Magic Furniture", Enable_MagicFurniture, is_magic_furniture_target, 30)
end

-- Magic Factories
local function MagicFactories()
    patch_magic_storage_targets("Magic Factories", Enable_MagicFactories, is_magic_factory_target, 25)
end

local function ApplyExtendedMagicStorage()
    MagicFurniture()
    MagicFactories()
end

return ApplyExtendedMagicStorage
