-- Generated ItemInfo visual-reference probe; research-only.
local DONOR_GUID = "01474f79-6b5a-4bcd-999d-7e9339fda91c"
local NEW_ITEM_ID = 3987654601
local REPLACEMENT_MODEL = "159b5f47-aa61-4db9-8e64-06db850de6f6"
local function log(kind, value)
    print("[CC-ITEM-VISUAL:item_visual_candidate_159b_1076226] " .. kind .. "|" .. tostring(value or ""))
end
local donor
for _, resource in pairs(game.assets.get_resources_by_type('keen::ItemInfo') or {}) do
    if resource and tostring(resource.guid) == DONOR_GUID then donor = resource; break end
end
if not donor then log("DONOR", "missing"); return {} end
local ok_clone, clone = pcall(function()
    return game.assets.register_resource(donor.data, 'keen::ItemInfo')
end)
if not ok_clone or not clone then log("CLONE_ERROR", tostring(clone)); return {} end
clone.data.itemId.value = NEW_ITEM_ID
local before = clone.data.iconModel
local ok_assign, assign_error = pcall(function()
    clone.data.iconModel = REPLACEMENT_MODEL
end)
log("ASSIGN", tostring(ok_assign) .. "|" .. tostring(assign_error or ""))
log("BEFORE", tostring(before and before.guid or before and before.value or before or "nil"))
log("AFTER", tostring(clone.data.iconModel and clone.data.iconModel.guid or clone.data.iconModel and clone.data.iconModel.value or clone.data.iconModel or "nil"))
log("ACTION", "clone_only_no_registry_mutation")
return {}
