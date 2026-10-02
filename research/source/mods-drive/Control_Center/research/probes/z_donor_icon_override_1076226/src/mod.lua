local TARGET_ITEM_ID = 3987654333
local DONOR_ICON_GUID = 'b7eb722c-ed5d-48d8-93c8-a68f6ef342d0'
local PREFIX = '[CC-DONOR-ICON-OVERRIDE] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end

local function resources(type_name)
    local ok, result = pcall(function() return game.assets.get_resources_by_type(type_name) or {} end)
    if not ok then log('ERROR', type_name .. '|' .. tostring(result)); return {} end
    return result
end

local item
for _, candidate in pairs(resources('keen::ItemInfo')) do
    if candidate and candidate.data and candidate.data.itemId
        and candidate.data.itemId.value == TARGET_ITEM_ID then
        item = candidate
        break
    end
end
if not item then log('STOP', 'target_item_not_found'); return {} end

local icon_donor
for _, texture in pairs(resources('keen::UiTextureResource')) do
    if texture and tostring(texture.guid) == DONOR_ICON_GUID then
        icon_donor = texture
        break
    end
end
if not icon_donor then log('STOP', 'icon_donor_not_found'); return {} end

local ok, clone = pcall(function()
    return game.assets.register_resource(icon_donor.data, 'keen::UiTextureResource')
end)
if not ok or not clone then log('STOP', 'icon_clone_failed|' .. tostring(clone)); return {} end
item.data.iconImage = clone.guid
log('ICON_OVERRIDE', 'item=' .. TARGET_ITEM_ID .. '|source=' .. DONOR_ICON_GUID .. '|new=' .. tostring(clone.guid))
return {}
