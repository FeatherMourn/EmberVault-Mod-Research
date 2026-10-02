-- Bounded, read-only inspection of ItemInfo.collectionInfo/category references.
local PREFIX = '[CC-COLLECTION-BOUNDARY] '
local function log(kind, ...) local a = {PREFIX .. kind}; for i=1,select('#',...) do a[#a+1]=tostring(select(i,...)) end; print(table.concat(a,'|')) end
local function resources(t)
    local ok, r = pcall(function() return game.assets.get_resources_by_type(t) or {} end)
    if not ok then log('ERROR', t, r); return {} end
    return r
end
local function val(x)
    if x == nil then return 'nil' end
    local ok, v = pcall(function() return x.value end)
    if ok and v ~= nil then return tostring(v) end
    return tostring(x)
end
for _, type_name in ipairs({'keen::ItemCollectionCategory', 'keen::ItemCollectionCategoryDirectory', 'keen::ItemCollectionSlotCategory', 'keen::ItemCollectionDirectory', 'keen::ItemCollectionSetup'}) do
    local found = resources(type_name)
    local n = 0
    for index, resource in pairs(found) do
        n = n + 1
        if n <= 4 then
            log('RESOURCE', 'type=' .. type_name, 'index=' .. tostring(index), 'guid=' .. tostring(resource.guid), 'data=' .. tostring(resource.data))
        end
    end
    log('RESOURCE_SUMMARY', 'type=' .. type_name, 'count=' .. n)
end
local count, matches = 0, 0
for _, item in pairs(resources('keen::ItemInfo')) do
    count = count + 1
    local data = item.data
    local item_id = data and data.itemId and data.itemId.value
    if item_id == 48042626 or item_id == 2940001508 then
        log('TARGET', 'guid=' .. tostring(item.guid), 'itemId=' .. tostring(item_id), 'debugName=' .. tostring(data.debugName), 'category=' .. tostring(data.category), 'equipmentSlot=' .. tostring(data.equipmentSlot), 'equipment=' .. tostring(data.equipment), 'itemClassAlignment=' .. tostring(data.itemClassAlignment), 'objectId=' .. tostring(data.objectId), 'collectionInfo=' .. tostring(data.collectionInfo))
    end
    local collection = data and data.collectionInfo
    if collection then
        matches = matches + 1
        local categories = collection.categories
        log('MATCH', 'guid=' .. tostring(item.guid), 'itemId=' .. val(data.itemId), 'collectionType=' .. type(collection), 'categoriesType=' .. type(categories), 'categories=' .. tostring(categories), 'overrideModel=' .. tostring(collection.overrideModel))
        local n = 0
        for index, category in pairs(categories or {}) do
            n = n + 1
            log('CATEGORY', 'itemId=' .. val(data.itemId), 'index=' .. tostring(index), 'valueType=' .. type(category), 'value=' .. tostring(category), 'categoryValue=' .. val(category and category.category))
            if n >= 8 then break end
        end
        -- Continue through the full ItemInfo set so the known blueprint donor
        -- can be compared with the furniture donor without broad payload reads.
    end
end
log('SUMMARY', 'itemsScanned=' .. count, 'collectionMatches=' .. matches, 'readOnly=true')
return {}
