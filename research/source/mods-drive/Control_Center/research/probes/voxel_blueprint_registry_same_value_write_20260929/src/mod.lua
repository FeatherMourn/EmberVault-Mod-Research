-- Research-only, reversible same-value write. No new entry or registration.
local function log(kind, value)
    print("[CC-BLUEPRINT-WRITE:same_value_20260929] " .. tostring(kind) .. "|" .. tostring(value or ""))
end
local guid = "3064d35d-7342-40ca-bdc9-aad58f83bf45"
local ok, resource = pcall(function()
    return game.assets.get_resource(guid, "keen::VoxelBlueprintItemRegistryResource", 0)
end)
log("LOOKUP", "ok=" .. tostring(ok) .. "|found=" .. tostring(resource ~= nil))
if not ok or not resource or not resource.data then return {} end
local items = resource.data.blueprintItems
local count = items and #items or 0
log("BEFORE", "count=" .. tostring(count))
if not items or count < 1 then log("RESULT", "no_entries"); return {} end
local first = items[1]
local size = first and first.size
if not size then log("RESULT", "missing_first_size"); return {} end
local old_x, old_y, old_z = size.x, size.y, size.z
local write_ok, write_err = pcall(function()
    size.x = old_x
    size.y = old_y
    size.z = old_z
end)
local after = first.size
log("WRITE", "ok=" .. tostring(write_ok) .. "|error=" .. tostring(write_err))
log("AFTER", "count=" .. tostring(#items) .. "|size=" .. tostring(after.x) .. "x" .. tostring(after.y) .. "x" .. tostring(after.z))
log("BOUNDARY", "created=false|registered=false|new_entry=false|menu=false|world=false|save=false")
log("RESULT", "same_value_write_complete")
return {}
