-- Runtime localization helper for EML/KFC content modules.
-- The game-side result is research-only until a controlled UI test confirms
-- that newly-created localization tags are consumed by the target build.
local M = {}

local COLLECTION_TYPE = 'keen::LocaTagCollectionResource'
local DATA_TYPE = 'keen::LocaTagCollectionResourceData'

function M.register_tag(english, description, explicit_guid)
    local value = {
        keenglish = tostring(english or ''),
        description = tostring(description or english or ''),
    }
    if explicit_guid then
        return game.assets.register_resource(value, 'keen::LocaTag', explicit_guid, 0)
    end
    return game.assets.register_resource(value, 'keen::LocaTag')
end

local function copy(value, seen)
    if type(value) ~= 'table' then return value end
    seen = seen or {}
    if seen[value] then return seen[value] end
    local out = {}
    seen[value] = out
    for key, child in pairs(value) do out[copy(key, seen)] = copy(child, seen) end
    return out
end

local function fnv1a32(key)
    -- Older EML builds did not expose the global hasher inside every module
    -- environment. Keep localization registration usable across those builds.
    local api = rawget(_G, 'hasher')
    if api and api.fnv1a32 then return api.fnv1a32(key) end
    local hash = 2166136261
    for index = 1, #key do
        hash = (hash ~ string.byte(key, index)) & 0xffffffff
        hash = (hash * 16777619) & 0xffffffff
    end
    return hash
end

local function tag_id(key)
    return { value = fnv1a32(key) }
end

local function content_for(hash, translations)
    local source = game.assets.get_content(game.guid.from_content_hash(hash))
    if not source then error('Localization content was not found') end
    local data = source:read_data():read_resource(DATA_TYPE)
    data.tags = data.tags or {}
    for key, text in pairs(translations or {}) do
        if text and tostring(text) ~= '' then
            table.insert(data.tags, {
                id = tag_id(key),
                text = tostring(text),
                arguments = {},
                genericArguments = 0,
            })
        end
    end
    local output = buffer.create()
    output:write_resource(DATA_TYPE, data)
    return game.assets.create_content(output)
end

-- entries is keyed by localization key, then by exact game locale (En_Us,
-- De_De, etc.). Missing locales fall back to default_locale.
function M.register(entries, new_locale_guid, default_locale)
    local original = game.assets.get_resources_by_type(COLLECTION_TYPE)[1]
    if not original then error('LocaTagCollectionResource was not found') end
    local collection = copy(original.data)
    local fallback = default_locale or 'En_Us'
    local by_language = {}

    for key, values in pairs(entries or {}) do
        local fallback_text = values[fallback]
        for locale, text in pairs(values or {}) do
            by_language[locale] = by_language[locale] or {}
            by_language[locale][key] = text
        end
        if fallback_text then
            for _, language in pairs(collection.languages or {}) do
                by_language[language.language] = by_language[language.language] or {}
                if by_language[language.language][key] == nil then
                    by_language[language.language][key] = fallback_text
                end
            end
        end
    end

    local english = by_language.En_Us or by_language[fallback] or {}
    collection.keenglishDataHash = content_for(collection.keenglishDataHash, english)
    for _, language in pairs(collection.languages or {}) do
        local translations = by_language[language.language] or english
        language.dataHash = content_for(language.dataHash, translations)
    end

    local registered = game.assets.register_resource(collection, COLLECTION_TYPE, new_locale_guid, 0)
    return registered
end

return M
