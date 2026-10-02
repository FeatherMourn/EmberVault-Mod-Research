-- Generated registry clone probe; research-only.
local DONOR_GUID = "01474f79-6b5a-4bcd-999d-7e9339fda91c"
local NEW_ITEM_ID = 3987654370
local function log(kind, value)
    print("[CC-REGISTRY-CLONE:registry_clone_probe_20260927_v22] " .. kind .. "|" .. tostring(value or ""))
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
local registry = (game.assets.get_resources_by_type('keen::ItemRegistryResource') or {})[1]
if not registry or not registry.data or not registry.data.itemRefs then
    log("REGISTRY", "missing")
    return {}
end
local before = 0
for _, _ in pairs(registry.data.itemRefs) do before = before + 1 end
table.insert(registry.data.itemRefs, result)
local after = 0
for _, _ in pairs(registry.data.itemRefs) do after = after + 1 end
log("REGISTRY", tostring(before) .. "->" .. tostring(after))
log("INDEXED_ITEM", NEW_ITEM_ID)
return {}
