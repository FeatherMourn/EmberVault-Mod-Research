local PREFIX = '[CC-TEMPLATE-INTERACTION-METADATA] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end

local ok, rows = pcall(function()
    return game.assets.get_resource_metadata_by_type('keen::TemplateResource', 8) or {}
end)
log('QUERY', 'ok=' .. tostring(ok) .. '|count=' .. tostring(ok and #rows or 0))
if ok then
    for _, row in ipairs(rows) do
        log('RESOURCE', 'guid=' .. tostring(row.guid or '') .. '|name=' .. tostring(row.debug_name or row.name or ''))
    end
end
return {}
