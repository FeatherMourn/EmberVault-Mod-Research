-- Generated registry clone probe; research-only.
local DONOR_GUID = "01474f79-6b5a-4bcd-999d-7e9339fda91c"
local NEW_ITEM_ID = 3987654375
local function log(kind, value)
    print("[CC-REGISTRY-CLONE:registry_clone_probe_20260927_v27] " .. kind .. "|" .. tostring(value or ""))
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
result.data.objectId = result.guid
if result.data.debugName then
    result.data.debugName = "CC_Generated_Clone_" .. tostring(NEW_ITEM_ID)
end
local registry
for _, candidate in pairs(game.assets.get_resources_by_type('keen::ItemRegistryResource') or {}) do
    if candidate and candidate.data and candidate.data.itemRefs then
        registry = candidate
        break
    end
end
if not registry or not registry.data or not registry.data.itemRefs then
    log("REGISTRY", "missing")
    return {}
end
local before = #registry.data.itemRefs
table.insert(registry.data.itemRefs, result)
if registry.data.dbgNames then
    table.insert(registry.data.dbgNames, result.data.debugName)
    log("DBG_NAMES", "updated")
else
    log("DBG_NAMES", "missing")
end
local after = #registry.data.itemRefs
log("REGISTRY", tostring(before) .. "->" .. tostring(after))
local found = false
for index = 1, #registry.data.itemRefs do
    local entry = registry.data.itemRefs[index]
    if entry and entry.data and entry.data.itemId and entry.data.itemId.value == NEW_ITEM_ID then
        found = true
        break
    end
end
log("INDEX_LOOKUP", tostring(found))
if found then log("INDEXED_ITEM", NEW_ITEM_ID) end
return {}
