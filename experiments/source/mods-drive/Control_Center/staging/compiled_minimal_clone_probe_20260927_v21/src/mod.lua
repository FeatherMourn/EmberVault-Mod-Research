-- Minimal generated clone probe; research-only.
local DONOR_GUID = "01474f79-6b5a-4bcd-999d-7e9339fda91c"
local NEW_ITEM_ID = 3987654369
local function log(kind, value)
    print("[CC-MINIMAL-CLONE:minimal_clone_probe_20260927_v21] " .. kind .. "|" .. tostring(value or ""))
end
local items = game.assets.get_resources_by_type('keen::ItemInfo') or {}
local donor
for _, resource in pairs(items) do
    if resource and tostring(resource.guid) == DONOR_GUID then donor = resource; break end
end
log("DONOR", tostring(donor ~= nil))
if not donor then return {} end
local ok, result = pcall(function()
    return game.assets.register_resource(donor.data, 'keen::ItemInfo')
end)
log("REGISTER", tostring(ok) .. "|" .. tostring(result))
if not ok or not result then return {} end
result.data.itemId.value = NEW_ITEM_ID
log("CLONED_ITEM", NEW_ITEM_ID)
return {}
