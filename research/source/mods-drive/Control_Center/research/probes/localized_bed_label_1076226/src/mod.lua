-- Controlled label-consumption probe for the already-registered bed fixture.
local PREFIX = '[CC-LOCALIZED-BED] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function resources(type_name)
    local ok, result = pcall(function() return game.assets.get_resources_by_type(type_name) or {} end)
    if not ok then log('ERROR', type_name .. '|' .. tostring(result)); return {} end
    return result
end
local target
for _, item in pairs(resources('keen::ItemInfo')) do
    if item and item.data and item.data.itemId and item.data.itemId.value == 3987654321 then target = item; break end
end
if not target then log('STOP', 'verified_bed_clone_not_found'); return {} end
local tag_ok, tag = pcall(function()
    return require('kfc_localization_registry').register_tag('Control Center Localized Bed', 'A runtime localization UI test bed')
end)
log('LOCALIZATION_TAG', 'ok=' .. tostring(tag_ok) .. '|result=' .. tostring(tag_ok and tag and tag.guid or tag))
if tag_ok and tag then
    target.data.name = tag.guid
    target.data.description = tag.guid
    log('DISPLAY_FIELDS', 'name=' .. tostring(target.data.name) .. '|description=' .. tostring(target.data.description))
else
    log('STOP', 'localization_tag_failed')
end
return {}
