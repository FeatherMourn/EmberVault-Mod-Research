local PREFIX = '[CC-ICON-ZERO-BOUNDARY] '
local ZERO = '00000000-0000-0000-0000-000000000000'
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local ok, list = pcall(function() return game.assets.get_resources_by_type('keen::ItemInfo') or {} end)
if not ok then log('STOP', tostring(list)); return {} end
local donor
for _, item in pairs(list) do
    if item and item.data and item.data.itemId and item.data.itemId.value == 2940001508 then donor = item; break end
end
if not donor then log('STOP', 'donor_not_found'); return {} end
local ok_clone, clone = pcall(function() return game.assets.register_resource(donor.data, 'keen::ItemInfo') end)
if not ok_clone or not clone then log('STOP', 'clone_failed|' .. tostring(clone)); return {} end
log('CLONE', tostring(clone.guid))
local function attempt(label, fn)
    local good, value = pcall(fn)
    log(label, 'ok=' .. tostring(good) .. '|value=' .. tostring(good and value or value))
end
attempt('MODEL_ZERO', function() clone.data.iconModel = ZERO; return clone.data.iconModel end)
attempt('SCENE_ZERO', function() clone.data.iconScene = ZERO; return clone.data.iconScene end)
log('FINAL', 'model=' .. tostring(clone.data.iconModel) .. '|scene=' .. tostring(clone.data.iconScene))
return {}
