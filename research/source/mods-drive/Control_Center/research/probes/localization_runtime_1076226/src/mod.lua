-- Deterministic Control Center localization probe.
local registry = require('kfc_localization_registry')
local entries = {
  ["control_center.demo_name"] = {
    ["De_De"] = "Control-Center-Demo",
    ["En_Us"] = "Control Center Demo",
  },
}
local tag_ok, tag = pcall(function() return registry.register_tag('Control Center Demo', 'Control Center localization probe') end)
print('[CC-LOCALIZATION] TAG|ok=' .. tostring(tag_ok) .. '|result=' .. tostring(tag_ok and tag and tag.guid or tag))
local ok, result = pcall(function() return registry.register(entries, "882e1edc-ee55-5205-8d10-074558b52947", 'En_Us') end)
print('[CC-LOCALIZATION] REGISTER|ok=' .. tostring(ok) .. '|result=' .. tostring(ok and result and result.guid or result))
print('[CC-LOCALIZATION] WARNING|UI_consumption_requires_controlled_validation')
return {}
