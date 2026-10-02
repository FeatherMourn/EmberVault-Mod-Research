-- Research-only isolated ItemInfo + blueprint registry registration.
local function log(kind, value)
    print("[CC-BLUEPRINT-REGISTER:registration_20260929] " .. tostring(kind) .. "|" .. tostring(value or ""))
end
local NEW_ID = 3990000001
local NEW_GUID = "c8a4b2e1-5a63-4d91-8ed6-7f4b2c1a9001"
local DONOR_ID = 48042626
local function find_item(id)
    for _, r in ipairs(game.assets.get_resources_by_type("keen::ItemInfo") or {}) do
        if r and r.data and r.data.itemId and r.data.itemId.value == id then return r end
    end
end
local function find_resource(t)
    local all = game.assets.get_resources_by_type(t) or {}
    return all[1]
end
local donor = find_item(DONOR_ID)
local item_registry = find_resource("keen::ItemRegistryResource")
local blueprint_registry = find_resource("keen::VoxelBlueprintItemRegistryResource")
log("LOOKUP", "donor=" .. tostring(donor ~= nil) .. "|item_registry=" .. tostring(item_registry ~= nil) .. "|blueprint_registry=" .. tostring(blueprint_registry ~= nil))
if not donor or not item_registry or not blueprint_registry then return {} end
local source_blueprint
for _, bp in ipairs(blueprint_registry.data.blueprintItems or {}) do
    if bp and bp.itemId and bp.itemId.value == DONOR_ID then source_blueprint = bp; break end
end
log("DONOR", "blueprint=" .. tostring(source_blueprint ~= nil))
if not source_blueprint then return {} end
local create_ok, new_item, create_err = false, nil, nil
create_ok, new_item = pcall(function()
    return game.assets.create_resource(donor.data, "keen::ItemInfo", NEW_GUID, 0)
end)
if not create_ok then create_err = tostring(new_item); new_item = nil end
log("CREATE_ITEM", "ok=" .. tostring(create_ok) .. "|guid=" .. tostring(new_item and new_item.guid) .. "|error=" .. tostring(create_err))
if not new_item or not new_item.data then return {} end
local edit_ok, edit_err = pcall(function()
    new_item.data.itemId.value = NEW_ID
    new_item.data.debugName = "CC_Blueprint_Registration_Probe"
    new_item.data.objectId = new_item.guid
end)
log("EDIT_ITEM", "ok=" .. tostring(edit_ok) .. "|error=" .. tostring(edit_err))
local bp_before = #blueprint_registry.data.blueprintItems
local item_before = #item_registry.data.itemRefs
local donor_id_before = source_blueprint.itemId and source_blueprint.itemId.value
local cloned_blueprint = {
    itemId = {value = NEW_ID},
    size = {x = source_blueprint.size.x, y = source_blueprint.size.y, z = source_blueprint.size.z},
    data = source_blueprint.data,
    isDataCompressed = source_blueprint.isDataCompressed,
}
local bp_insert_ok, bp_insert_err = pcall(function() table.insert(blueprint_registry.data.blueprintItems, cloned_blueprint) end)
local bp_index = #blueprint_registry.data.blueprintItems
local bp_edit_ok, bp_edit_err = false, nil
if bp_insert_ok and bp_index == bp_before + 1 then
    bp_edit_ok, bp_edit_err = pcall(function() bp_edit_ok = blueprint_registry.data.blueprintItems[bp_index].itemId.value == NEW_ID end)
end
log("BLUEPRINT", "insert_ok=" .. tostring(bp_insert_ok) .. "|insert_error=" .. tostring(bp_insert_err) .. "|edit_ok=" .. tostring(bp_edit_ok) .. "|edit_error=" .. tostring(bp_edit_err) .. "|count=" .. tostring(#blueprint_registry.data.blueprintItems) .. "|donor_id_before=" .. tostring(donor_id_before) .. "|donor_id_after=" .. tostring(source_blueprint.itemId and source_blueprint.itemId.value))
local item_insert_ok, item_insert_err = pcall(function() table.insert(item_registry.data.itemRefs, new_item) end)
log("ITEM_REGISTRY", "insert_ok=" .. tostring(item_insert_ok) .. "|error=" .. tostring(item_insert_err) .. "|count=" .. tostring(#item_registry.data.itemRefs))
local found_link = false
for _, ref in ipairs(item_registry.data.itemRefs or {}) do
    local ok, resolved = pcall(function() return game.assets.get_resource(ref, "keen::ItemInfo", 0) end)
    if ok and resolved and tostring(resolved.guid) == NEW_GUID then found_link = true; break end
end
local found_bp = false
for _, bp in ipairs(blueprint_registry.data.blueprintItems or {}) do
    if bp and bp.itemId and bp.itemId.value == NEW_ID then found_bp = true; break end
end
log("VALIDATE", "item_link=" .. tostring(found_link) .. "|blueprint_link=" .. tostring(found_bp))
log("BOUNDARY", "created=true|registered=" .. tostring(item_insert_ok and found_link) .. "|menu=false|world=false|save=false")
log("RESULT", "registration_complete")
return {}
