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
print('[CC-LOCALIZATION] COLLECTION|skipped=safe_default_requires_explicit_opt_in')
print('[CC-LOCALIZATION] WARNING|UI_consumption_requires_controlled_validation')
return {}
