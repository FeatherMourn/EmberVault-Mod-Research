-- Probe-local guarded registration helper.
local M = {}
function M.clone_resource(donor, type_name, explicit_guid, part)
    if not donor or not donor.data then return nil, 'donor_data_missing' end
    local ok, result = pcall(function()
        return game.assets.register_resource(donor.data, type_name, explicit_guid, part)
    end)
    if not ok then return nil, 'resource_registration_failed:' .. tostring(result) end
    return result, nil
end
return M
