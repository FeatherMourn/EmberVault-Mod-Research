-- Generated read-only metadata policy probe.
local PREFIX = '[CC-METADATA-SUITE] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end

local TYPE_NAME = "keen::ItemInfo"
log('BEFORE|' .. TYPE_NAME)
local ok, rows = pcall(function() return game.assets.get_resource_metadata_by_type(TYPE_NAME) or {} end)
local count = 0; for _ in pairs(rows or {}) do count = count + 1 end
log('RESULT|' .. TYPE_NAME .. '|ok=' .. tostring(ok) .. '|count=' .. tostring(count))

local TYPE_NAME = "keen::ItemRegistryResource"
log('BEFORE|' .. TYPE_NAME)
local ok, rows = pcall(function() return game.assets.get_resource_metadata_by_type(TYPE_NAME) or {} end)
local count = 0; for _ in pairs(rows or {}) do count = count + 1 end
log('RESULT|' .. TYPE_NAME .. '|ok=' .. tostring(ok) .. '|count=' .. tostring(count))

local TYPE_NAME = "keen::RecipeRegistryResource"
log('BEFORE|' .. TYPE_NAME)
local ok, rows = pcall(function() return game.assets.get_resource_metadata_by_type(TYPE_NAME) or {} end)
local count = 0; for _ in pairs(rows or {}) do count = count + 1 end
log('RESULT|' .. TYPE_NAME .. '|ok=' .. tostring(ok) .. '|count=' .. tostring(count))

local TYPE_NAME = "keen::ItemKnowledgeResource"
log('BEFORE|' .. TYPE_NAME)
local ok, rows = pcall(function() return game.assets.get_resource_metadata_by_type(TYPE_NAME) or {} end)
local count = 0; for _ in pairs(rows or {}) do count = count + 1 end
log('RESULT|' .. TYPE_NAME .. '|ok=' .. tostring(ok) .. '|count=' .. tostring(count))

local TYPE_NAME = "keen::FbUiBundle"
log('BEFORE|' .. TYPE_NAME)
local ok, rows = pcall(function() return game.assets.get_resource_metadata_by_type(TYPE_NAME) or {} end)
local count = 0; for _ in pairs(rows or {}) do count = count + 1 end
log('RESULT|' .. TYPE_NAME .. '|ok=' .. tostring(ok) .. '|count=' .. tostring(count))

return {}
