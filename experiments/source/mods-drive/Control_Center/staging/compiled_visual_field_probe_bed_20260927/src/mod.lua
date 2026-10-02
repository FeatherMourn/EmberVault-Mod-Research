-- Generated donor visual-field probe; research-only and read-only.
local DONOR_GUID = "01474f79-6b5a-4bcd-999d-7e9339fda91c"
local function log(kind, value)
    print("[CC-VISUAL-FIELDS:visual_field_probe_bed_20260927] " .. kind .. "|" .. tostring(value or ""))
end
local donor
for _, resource in pairs(game.assets.get_resources_by_type('keen::ItemInfo') or {}) do
    if resource and tostring(resource.guid) == DONOR_GUID then donor = resource; break end
end
if not donor or not donor.data then log("DONOR", "missing"); return {} end
log("DONOR", tostring(donor.guid))
local visual_fields = {"iconImage", "iconModel", "iconScene", "visualModel", "visualEntity", "placedEntity", "material", "texture", "objectId"}
for _, field in ipairs(visual_fields) do
    local value = donor.data[field]
    log("FIELD", field .. "|" .. tostring(value ~= nil) .. "|" .. tostring(value and value.guid or value and value.value or value or "nil"))
end
log("ACTION", "read_only_field_inventory")
return {}
