-- Read-only probe: identify typed FbUiBundle containers relevant to catalog UI.
local PREFIX = '[CC-FBUI-STRUCTURE] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function resources(type_name)
    local ok, result = pcall(function() return game.assets.get_resources_by_type(type_name) or {} end)
    if not ok then log('ERROR', type_name .. '|' .. tostring(result)); return {} end
    return result
end
local function describe(label, value)
    if value == nil then log('FIELD', label .. '|nil'); return end
    if type(value) ~= 'table' then log('FIELD', label .. '|lua_type=' .. type(value)); return end
    local count = 0
    local samples = {}
    for key, child in pairs(value) do
        count = count + 1
        if #samples < 12 then
            samples[#samples + 1] = tostring(key) .. ':' .. type(child)
        end
    end
    log('FIELD', label .. '|lua_type=table|count=' .. count .. '|samples=' .. table.concat(samples, ','))
end

local bundles = resources('keen::FbUiBundle')
local count = 0
for _, bundle in pairs(bundles) do
    count = count + 1
    local data = bundle and bundle.data
    if data then
        describe('icons', data.icons)
        describe('menu', data.menu)
        describe('itemSlot', data.itemSlot)
        if data.menu then
            describe('menu.crafting', data.menu.crafting)
            local crafting = data.menu.crafting
            if crafting then
                describe('menu.crafting.recipes', crafting.recipes)
                local recipes = crafting.recipes
                if recipes then describe('menu.crafting.recipes.trees', recipes.trees) end
            end
        end
    else
        log('BUNDLE', 'missing_data')
    end
end
log('BUNDLES', count)
log('WARNING', 'read_only_structure_only')
return {}
