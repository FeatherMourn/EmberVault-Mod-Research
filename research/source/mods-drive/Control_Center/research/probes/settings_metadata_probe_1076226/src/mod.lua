-- Read-only settings-family identity probe; never decodes or writes payloads.
local TYPES = {
    "keen::GameSettingsPresetsResource",
    "keen::FbUiBundle"
}

local function log(kind, value)
    print("[CC-SETTINGS-METADATA:settings_metadata_probe_1076226] " .. kind .. "|" .. tostring(value or ""))
end

for _, type_name in ipairs(TYPES) do
    log("BEGIN", type_name)
    local ok, rows = pcall(function()
        return game.assets.get_resource_metadata_by_type(type_name)
    end)
    log("CALL", type_name .. "|" .. tostring(ok))
    if ok and rows then
        log("COUNT", type_name .. "|" .. tostring(#rows))
        for _, row in ipairs(rows) do
            log("RESOURCE", type_name .. "|" .. tostring(row.guid) .. "|" .. tostring(row.part))
        end
    else
        log("ERROR", type_name .. "|" .. tostring(rows))
    end
end

log("ACTION", "metadata_only_no_decode_no_write")
return {}
