-- Research-only. Insert a cloned donor value, edit its identity, then remove it.
local function log(kind, value)
    print("[CC-BLUEPRINT-IDENTITY:new_identity_20260929] " .. tostring(kind) .. "|" .. tostring(value or ""))
end
local guid = "3064d35d-7342-40ca-bdc9-aad58f83bf45"
local NEW_ID = 3990000001
local ok, resource = pcall(function()
    return game.assets.get_resource(guid, "keen::VoxelBlueprintItemRegistryResource", 0)
end)
log("LOOKUP", "ok=" .. tostring(ok) .. "|found=" .. tostring(resource ~= nil))
if not ok or not resource or not resource.data then return {} end
local items = resource.data.blueprintItems
local before = items and #items or 0
if not items or before < 1 then log("RESULT", "no_entries"); return {} end
local donor_id = items[1].itemId and items[1].itemId.value
log("BEFORE", "count=" .. tostring(before) .. "|donor_id=" .. tostring(donor_id))
local insert_ok, insert_err = pcall(function() table.insert(items, items[1]) end)
local inserted_index = #items
log("INSERT", "ok=" .. tostring(insert_ok) .. "|error=" .. tostring(insert_err) .. "|count=" .. tostring(inserted_index))
local edit_ok, edit_err = false, nil
if insert_ok and inserted_index == before + 1 then
    edit_ok, edit_err = pcall(function() items[inserted_index].itemId.value = NEW_ID end)
end
local inserted_id = items[inserted_index] and items[inserted_index].itemId and items[inserted_index].itemId.value
local donor_after = items[1].itemId and items[1].itemId.value
log("IDENTITY", "ok=" .. tostring(edit_ok) .. "|error=" .. tostring(edit_err) .. "|new_id=" .. tostring(inserted_id) .. "|donor_after=" .. tostring(donor_after))
local remove_ok, remove_err = false, nil
if insert_ok then remove_ok, remove_err = pcall(function() table.remove(items, inserted_index) end) end
log("REMOVE", "ok=" .. tostring(remove_ok) .. "|error=" .. tostring(remove_err) .. "|count=" .. tostring(#items))
log("BOUNDARY", "new_identity=" .. tostring(inserted_id == NEW_ID and donor_after == donor_id) .. "|registered=false|menu=false|world=false|save=false")
log("RESULT", "new_identity_insert_edit_remove_complete")
return {}
