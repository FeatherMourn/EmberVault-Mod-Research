local GUID = "46e14df6-fb8f-4f66-9463-e23b9e19e48e"
local TYPE = "keen::GameSettingsPresetsResource"
local prefix = "[CC-SETTINGS-WRITE:settings_single_write_probe_1076226] "
print(prefix .. "BEGIN")
local ok, resource = pcall(function() return game.assets.get_resource(GUID, TYPE, 0) end)
print(prefix .. "LOOKUP|" .. tostring(ok) .. "|" .. tostring(resource ~= nil))
if not ok or not resource or not resource.data then return {} end
local data = resource.data
local read_ok, current = pcall(function() return data.minValues.enemyDamageFactor end)
print(prefix .. "READ|" .. tostring(read_ok) .. "|" .. tostring(current))
if not read_ok or current == nil then return {} end
local write_ok, write_result = pcall(function()
    data.minValues.enemyDamageFactor = current
    return data.minValues.enemyDamageFactor
end)
print(prefix .. "WRITE_SAME|" .. tostring(write_ok) .. "|" .. tostring(write_result))
print(prefix .. "ACTION|single_same_value_write_only")
return {}
