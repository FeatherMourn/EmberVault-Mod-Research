-- Research-only, reversible same-entry insert/remove. No new identity.
local function log(kind, value)
    print("[CC-BLUEPRINT-INSERT:insert_remove_20260929] " .. tostring(kind) .. "|" .. tostring(value or ""))
end
local guid = "3064d35d-7342-40ca-bdc9-aad58f83bf45"
local ok, resource = pcall(function()
    return game.assets.get_resource(guid, "keen::VoxelBlueprintItemRegistryResource", 0)
end)
log("LOOKUP", "ok=" .. tostring(ok) .. "|found=" .. tostring(resource ~= nil))
if not ok or not resource or not resource.data then return {} end
local items = resource.data.blueprintItems
local before = items and #items or 0
log("BEFORE", "count=" .. tostring(before))
if not items or before < 1 then log("RESULT", "no_entries"); return {} end
local insert_ok, insert_err = pcall(function() table.insert(items, items[1]) end)
local after_insert = #items
log("INSERT", "ok=" .. tostring(insert_ok) .. "|error=" .. tostring(insert_err) .. "|count=" .. tostring(after_insert))
local remove_ok, remove_err = false, nil
if insert_ok and after_insert == before + 1 then
    remove_ok, remove_err = pcall(function() table.remove(items, after_insert) end)
end
log("REMOVE", "ok=" .. tostring(remove_ok) .. "|error=" .. tostring(remove_err) .. "|count=" .. tostring(#items))
log("BOUNDARY", "new_identity=false|registered=false|menu=false|world=false|save=false")
log("RESULT", "insert_remove_complete")
return {}
