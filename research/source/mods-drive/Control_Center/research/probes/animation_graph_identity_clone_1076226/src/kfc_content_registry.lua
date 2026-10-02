local M = {}

function M.clone_resource(donor, type_name, explicit_guid, part)
    if not donor or not donor.data then return nil, 'donor_data_missing' end
    if type(type_name) ~= 'string' or type_name == '' then return nil, 'resource_type_missing' end
    if type(explicit_guid) ~= 'string' or explicit_guid == '' then return nil, 'explicit_guid_missing' end
    if type(part) ~= 'number' then return nil, 'part_must_be_number' end
    local ok, result = pcall(function()
        return game.assets.register_resource(donor.data, type_name, explicit_guid, part)
    end)
    if not ok then return nil, 'resource_registration_failed:' .. tostring(result) end
    return result, nil
end

return M
