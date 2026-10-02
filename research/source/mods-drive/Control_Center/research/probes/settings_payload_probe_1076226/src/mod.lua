-- Read-only payload probe. It never assigns or registers a resource.
local GUID = "46e14df6-fb8f-4f66-9463-e23b9e19e48e"
local TYPE = "keen::GameSettingsPresetsResource"
print("[CC-SETTINGS-PAYLOAD:settings_payload_probe_1076226] BEGIN|" .. GUID)
local ok, resource = pcall(function()
    return game.assets.get_resource(GUID, TYPE, 0)
end)
print("[CC-SETTINGS-PAYLOAD:settings_payload_probe_1076226] CALL|" .. tostring(ok))
if not ok then
    print("[CC-SETTINGS-PAYLOAD:settings_payload_probe_1076226] ERROR|" .. tostring(resource))
    return {}
end
print("[CC-SETTINGS-PAYLOAD:settings_payload_probe_1076226] RESULT|" .. tostring(resource ~= nil))
if resource then
    local data_ok, data = pcall(function() return resource.data end)
    print("[CC-SETTINGS-PAYLOAD:settings_payload_probe_1076226] DATA|" .. tostring(data_ok) .. "|" .. tostring(data ~= nil))
end
print("[CC-SETTINGS-PAYLOAD:settings_payload_probe_1076226] ACTION|read_only_no_write")
return {}
