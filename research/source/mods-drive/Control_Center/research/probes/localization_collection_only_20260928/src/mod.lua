local registry = require('kfc_localization_registry')
local function log(kind, value) print('[CC-LOCALIZATION-COLLECTION] ' .. kind .. '|' .. tostring(value or '')) end
log('START', 'locales=En_Us')
local tag_ok, tag = pcall(function()
    return registry.register_tag('Control Center Collection Probe', 'Collection transition probe')
end)
log('TAG', 'ok=' .. tostring(tag_ok) .. '|result=' .. tostring(tag_ok and tag and tag.guid or tag))
if not tag_ok then return {} end
log('BEFORE_COLLECTION', 'tag_registered=true')
local collection_ok, collection = pcall(function()
    return registry.register({['Control Center Collection Probe'] = {En_Us = 'Control Center Collection Probe'}}, '8b1e4f67-2a9d-5c30-b8e1-4d7f6a2c9013', 'En_Us', {"En_Us"})
end)
log('COLLECTION', 'ok=' .. tostring(collection_ok) .. '|result=' .. tostring(collection_ok and collection and collection.guid or collection))
log('AFTER_COLLECTION', 'returned=true')
local ok_items, items = pcall(function() return game.assets.get_resources_by_type('keen::ItemInfo') or {} end)
log('AFTER_COLLECTION_LOOKUP', 'ok=' .. tostring(ok_items) .. '|count=' .. tostring(ok_items and #items or 0))
return {}
