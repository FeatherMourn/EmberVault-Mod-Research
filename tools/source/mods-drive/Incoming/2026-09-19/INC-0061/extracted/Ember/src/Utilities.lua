-- ========================================
--                HELPERS
-- ========================================

function try(fn)
    local ok, res = pcall(fn)
    if ok then return true, res end
    return false, res
end

function get_first_resource_by_type(typeName)
    local list = game.assets.get_resources_by_type(typeName)
    if list and #list > 0 then return list[1] end
    return nil
end

function find_component_by_type(components, typeName)
    if not components then return nil end
    for _, c in ipairs(components) do
        if c and c.type == typeName then
            return c
        end
    end
    return nil
end
