-- EmberVault EML/KFC4 platform inventory probe, version 1.
-- Source template only: do not install or execute without explicit approval.
-- Read-only: no resource mutation, creation, patching, save access, or runtime hooks.

local lines = {
    "schema_version=1",
    "probe_id=platform-inventory",
    "evidence_state=observed-or-partial",
    "limitations=resource metadata only; no universal runtime or behavior claim",
}

local function add_error(scope, message)
    table.insert(lines, "error\t" .. tostring(scope) .. "\t" .. tostring(message))
end

local ok_types, resource_types = pcall(function()
    return game.assets.get_resource_types()
end)

if not ok_types then
    add_error("get_resource_types", resource_types)
else
    for _, resource_type in ipairs(resource_types) do
        table.insert(lines, "type\t" .. tostring(resource_type))

        -- This call is intentionally read-only. Per-type failures are retained
        -- so one unsupported type cannot abort the complete inventory.
        local ok_resources, resources = pcall(function()
            return game.assets.get_resources_by_type(resource_type)
        end)
        if not ok_resources then
            add_error("get_resources_by_type:" .. tostring(resource_type), resources)
        else
            for _, resource in ipairs(resources) do
                table.insert(lines, table.concat({
                    "resource",
                    tostring(resource.guid),
                    tostring(resource.type),
                    tostring(resource.part_index),
                }, "\t"))
            end
        end
    end
end

-- io.export is confined by EML to the configured export directory.
io.export("embervault/platform-inventory-v1.tsv", table.concat(lines, "\n"))
