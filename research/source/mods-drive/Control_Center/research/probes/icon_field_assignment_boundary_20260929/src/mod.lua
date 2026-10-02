local PREFIX = '[CC-ICON-FIELD-BOUNDARY] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function items()
    local ok, result = pcall(function() return game.assets.get_resources_by_type('keen::ItemInfo') or {} end)
    if not ok then log('ERROR', tostring(result)); return {} end
    return result
end
local donor
for _, item in pairs(items()) do
    if item and item.data and item.data.itemId and item.data.itemId.value == 2940001508 then donor = item; break end
end
if not donor then log('STOP', 'donor_not_found'); return {} end
local ok_clone, clone = pcall(function() return game.assets.register_resource(donor.data, 'keen::ItemInfo') end)
if not ok_clone or not clone then log('STOP', 'clone_failed|' .. tostring(clone)); return {} end
log('CLONE', 'guid=' .. tostring(clone.guid))
local function attempt(label, fn)
    local ok, value = pcall(fn)
    log(label, 'ok=' .. tostring(ok) .. '|value=' .. tostring(ok and value or value))
end
attempt('MODEL_CLEAR', function() clone.data.iconModel = nil; return clone.data.iconModel end)
attempt('SCENE_CLEAR', function() clone.data.iconScene = nil; return clone.data.iconScene end)
attempt('IMAGE_ASSIGN_ZERO', function()
    clone.data.iconImage = {value = '00000000-0000-0000-0000-000000000000'}
    return clone.data.iconImage
end)
log('FINAL', 'iconImage=' .. tostring(clone.data.iconImage) .. '|iconModel=' .. tostring(clone.data.iconModel) .. '|iconScene=' .. tostring(clone.data.iconScene))
return {}
