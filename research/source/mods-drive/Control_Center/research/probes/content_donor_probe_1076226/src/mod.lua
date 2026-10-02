-- Control Center Content Donor Graph Probe
-- READ ONLY: enumerates resource identity and shallow link fields only.
local BUILD = '1076226'
local DONOR_ITEM_ID = 2940001508
local DONOR_NAME = 'Prop_Decoration_Comfort2_T1_Bed'
local DONOR_GUID = '01474f79-6b5a-4bcd-999d-7e9339fda91c'
local ITEM_NAMES = {}
local PREFIX = '[CC-CONTENT-PROBE] '
local function log(kind, ...)
    local parts = { PREFIX .. kind }
    for i = 1, select('#', ...) do parts[#parts + 1] = tostring(select(i, ...)) end
    print(table.concat(parts, '|'))
end

local function safe(value)
    if value == nil then return '<nil>' end
    local ok, result = pcall(function() return tostring(value) end)
    return ok and result or '<unprintable>'
end

local function identity(resource, index)
    local data = resource and resource.data
    if not data then
        log('RESOURCE', index, 'missing_data')
        return
    end
    log('ITEM', index,
        'guid=' .. safe(resource.guid),
        'itemId=' .. safe(data.itemId and data.itemId.value),
        'debugName=' .. safe(data.debugName),
        'category=' .. safe(data.category),
        'icon=' .. safe(data.icon),
        'equipment=' .. safe(data.equipment),
        'recipe=' .. safe(data.recipe),
        'blueprint=' .. safe(data.blueprint),
        'voxelObject=' .. safe(data.equipment and data.equipment.voxelObject))
end

local function inspect_donor(resource, index)
    local data = resource and resource.data
    local id = data and data.itemId and data.itemId.value
    if id ~= DONOR_ITEM_ID then return end
    log('DONOR',
        'index=' .. safe(index),
        'name=' .. safe(data.debugName),
        'guid=' .. safe(resource.guid),
        'itemId=' .. safe(id),
        'category=' .. safe(data.category),
        'itemKnowledge=' .. safe(data.itemKnowledge),
        'maxStackSize=' .. safe(data.maxStackSize),
        'requiredCraftingIngredients=' .. safe(data.equipment and data.equipment.requiredCraftingIngredients),
        'placedEntity=' .. safe(data.equipment and data.equipment.placedEntity),
        'placementAABBmin=' .. safe(data.equipment and data.equipment.placementAABBmin),
        'placementAABBmax=' .. safe(data.equipment and data.equipment.placementAABBmax),
        'placementColliders=' .. safe(data.equipment and data.equipment.placementColliders),
        'visualModels=' .. safe(data.equipment and data.equipment.visualModels),
        'comfort=' .. safe(data.comfort),
        'buff=' .. safe(data.buff),
        'allData=' .. safe(data))
end

local function value_contains(value, target, depth)
    if depth > 5 or value == nil then return false end
    local ok, result = pcall(function()
        if type(value) == 'number' then return value == target end
        if type(value) == 'table' then
            for _, child in pairs(value) do
                if value_contains(child, target, depth + 1) then return true end
            end
        end
        return false
    end)
    return ok and result or false
end

local function serialized_contains(value, needle)
    local ok, text = pcall(function() return tostring(value) end)
    return ok and text and string.find(text, needle, 1, true) ~= nil
end

local function enumerate(type_name, callback)
    local ok, resources = pcall(function()
        return game.assets.get_resources_by_type(type_name) or {}
    end)
    if not ok then
        log('ERROR', type_name, safe(resources))
        return
    end
    local count = 0
    for index, resource in pairs(resources) do
        count = count + 1
        callback(resource, index)
    end
    log('COUNT', type_name, count)
end

log('BEGIN', 'build=' .. BUILD)
enumerate('keen::ItemInfo', identity)
enumerate('keen::ds::ItemInfo', identity)
enumerate('keen::ItemInfo', inspect_donor)
enumerate('keen::ItemInfo', function(resource)
    local data = resource and resource.data
    local id = data and data.itemId and data.itemId.value
    if id then
        ITEM_NAMES[id] = safe(data.debugName)
    end
end)

enumerate('keen::RecipeRegistryResource', function(resource, index)
    local data = resource and resource.data
    log('RECIPE_REGISTRY', index,
        'guid=' .. safe(resource and resource.guid),
        'recipes=' .. safe(data and data.recipes),
        'itemRefs=' .. safe(data and data.itemRefs))
    if data and data.recipes then
        for recipe_index, recipe in pairs(data.recipes) do
            if value_contains(recipe, DONOR_ITEM_ID, 0) or serialized_contains(recipe, DONOR_GUID) then
                log('DONOR_RECIPE_MATCH', 'registry=' .. safe(index), 'recipeIndex=' .. safe(recipe_index), 'recipe=' .. safe(recipe))
                if recipe.input then
                    for input_index, input in pairs(recipe.input) do
                        local stack = input and input.itemStack
                        local item_id = stack and stack.item and stack.item.value
                        log('DONOR_RECIPE_INPUT',
                            'index=' .. safe(input_index),
                            'itemId=' .. safe(item_id),
                            'name=' .. safe(ITEM_NAMES[item_id]),
                            'count=' .. safe(stack and stack.count),
                            'itemRef=' .. safe(stack and stack.itemRef))
                    end
                end
                if recipe.output then
                    for output_index, output in pairs(recipe.output) do
                        log('DONOR_RECIPE_OUTPUT',
                            'index=' .. safe(output_index),
                            'itemId=' .. safe(output.item and output.item.value),
                            'name=' .. safe(ITEM_NAMES[output.item and output.item.value]),
                            'count=' .. safe(output.count),
                            'itemRef=' .. safe(output.itemRef))
                    end
                end
                log('DONOR_RECIPE_REQUIREMENTS',
                    'knowledge=' .. safe(recipe.knowledgeRequirement),
                    'workshopGuid=' .. safe(recipe.workshopGuid),
                    'workshopId=' .. safe(recipe.workshopId and recipe.workshopId.value),
                    'duration=' .. safe(recipe.craftingDuration and recipe.craftingDuration.value))
            end
        end
    end
end)
enumerate('keen::ds::RecipeRegistryResource', function(resource, index)
    local data = resource and resource.data
    log('RECIPE_REGISTRY_DS', index,
        'guid=' .. safe(resource and resource.guid),
        'recipes=' .. safe(data and data.recipes),
        'itemRefs=' .. safe(data and data.itemRefs))
end)

enumerate('keen::BuildingMaterialParametersResource', function(resource, index)
    local data = resource and resource.data
    log('BUILDING_MATERIALS', index,
        'guid=' .. safe(resource and resource.guid),
        'materials=' .. safe(data and data.materials))
end)

log('END', 'read_only=true')
return {}
