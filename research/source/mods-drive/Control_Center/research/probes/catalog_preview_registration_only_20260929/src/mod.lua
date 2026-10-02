local PREFIX = '[CC-CATALOG-REGISTRATION-ONLY] '
local NEW_ID = 3987654851
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function resources(t)
    local ok, r = pcall(function() return game.assets.get_resources_by_type(t) or {} end)
    if not ok then log('ERROR', tostring(r)); return {} end
    return r
end
local donor
for _, item in pairs(resources('keen::ItemInfo')) do
    if item and item.data and item.data.itemId and item.data.itemId.value == 2940001508 then donor = item; break end
end
if not donor then log('STOP', 'donor_not_found'); return {} end
local ok, clone = pcall(function() return game.assets.register_resource(donor.data, 'keen::ItemInfo') end)
if not ok or not clone then log('STOP', 'clone_failed|' .. tostring(clone)); return {} end
clone.data.itemId.value = NEW_ID
clone.data.debugName = 'CC_Catalog_Registration_Only'
clone.data.objectId = clone.guid
log('CLONE', tostring(clone.guid))
local item_registry
for _, resource in pairs(resources('keen::ItemRegistryResource')) do
    if resource and resource.data and resource.data.itemRefs then
        item_registry = resource
        break
    end
end
if not item_registry then log('STOP', 'item_registry_not_found'); return {} end
local item_before = #item_registry.data.itemRefs
local insert_ok, insert_error = pcall(function()
    table.insert(item_registry.data.itemRefs, clone)
    if item_registry.data.dbgNames then
        table.insert(item_registry.data.dbgNames, clone.data.debugName)
    end
end)
log('ITEM_REGISTRY', 'ok=' .. tostring(insert_ok) .. '|error=' .. tostring(insert_error) .. '|count=' .. tostring(#item_registry.data.itemRefs) .. '|before=' .. tostring(item_before) .. '|dbgNames=' .. tostring(item_registry.data.dbgNames and #item_registry.data.dbgNames or 'missing'))
local discovered = false
for _, ref in pairs(item_registry.data.itemRefs or {}) do
    if ref and ref.data and ref.data.itemId and ref.data.itemId.value == NEW_ID then
        discovered = true
        break
    end
end
log('DISCOVERED', tostring(discovered))
local function attempt(label, fn)
    local good, value = pcall(fn)
    log(label, 'ok=' .. tostring(good) .. '|value=' .. tostring(good and value or value))
end
attempt('MODEL_ZERO', function() clone.data.iconModel = '00000000-0000-0000-0000-000000000000'; return clone.data.iconModel end)
attempt('SCENE_ZERO', function() clone.data.iconScene = '00000000-0000-0000-0000-000000000000'; return clone.data.iconScene end)
attempt('IMAGE_ZERO', function() clone.data.iconImage = '00000000-0000-0000-0000-000000000000'; return clone.data.iconImage end)
local found = false
for _, item in pairs(resources('keen::ItemInfo')) do
    if item and item.data and item.data.itemId and item.data.itemId.value == NEW_ID then found = true; break end
end
log('DISCOVERED', tostring(found))
log('COMPLETE', 'registration_only=true|recipe_mutation=false|ui_mutation=false')
return {}
