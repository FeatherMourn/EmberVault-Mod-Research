local M = {}
function M.read_mapped_variant(value)
    if value == nil then return { available = false, error = 'value_missing' } end
    local ok_type, variant_type = pcall(function() return value.type end)
    local ok_value, payload = pcall(function() return value.value end)
    if not ok_type or not ok_value then return { available = false, error = 'mapped_variant_read_failed' } end
    return { available = true, variant_type = variant_type, payload = payload }
end
function M.try_pairs(value)
    local ok, iterator, state, initial = pcall(pairs, value)
    if not ok then return nil, nil, nil, 'pairs_failed:' .. tostring(iterator) end
    return iterator, state, initial, nil
end
return M
