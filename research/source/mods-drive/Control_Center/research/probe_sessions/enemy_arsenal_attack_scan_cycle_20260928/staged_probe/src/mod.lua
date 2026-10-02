-- Bounded read-only scan for an attack donor with a populated action graph.
local TYPE_NAME = 'keen::enemy::EnemyArsenalRegistryResource'
local PREFIX = '[CC-ENEMY-ARSENAL-SCAN:enemy_arsenal_attack_scan_probe_1076226] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function text(value)
    local ok, result = pcall(function() return 'type=' .. type(value) .. '|text=' .. tostring(value) end)
    return ok, result
end
local function count_pairs(value, limit)
    local count = 0
    local ok = pcall(function()
        for key, child in pairs(value or {}) do
            count = count + 1
            if count <= (limit or 8) then
                local _, rendered = text(child)
                log('ENTRY', tostring(key) .. '|' .. tostring(rendered))
            end
        end
    end)
    return ok, count
end
local ok, resources = pcall(function() return game.assets.get_resources_by_type(TYPE_NAME) or {} end)
log('RESULT', 'ok=' .. tostring(ok))
if ok then
    local resource
    for _, candidate in pairs(resources) do resource = candidate; break end
    local data = resource and resource.data
    local arsenal_count, attack_count, populated = 0, 0, 0
    for arsenal_key, arsenal in pairs(data and data.arsenals or {}) do
        arsenal_count = arsenal_count + 1
        if arsenal_count <= 32 then
            for attack_key, attack in pairs(arsenal.attacks or {}) do
                attack_count = attack_count + 1
                if attack_count <= 24 then
                    local description = attack.description
                    local desc_text = description and description.actionSequence or nil
                    local actions_ok, actions_count = count_pairs(attack.actions, 4)
                    local commands_ok, commands_count = count_pairs(attack.commands, 4)
                    if (actions_count or 0) > 0 or (commands_count or 0) > 0 or desc_text ~= nil then
                        populated = populated + 1
                        log('DONOR', 'arsenal=' .. tostring(arsenal_key) .. '|attack=' .. tostring(attack_key) .. '|actionSequence=' .. tostring(desc_text) .. '|actions_ok=' .. tostring(actions_ok) .. '|actions=' .. tostring(actions_count) .. '|commands_ok=' .. tostring(commands_ok) .. '|commands=' .. tostring(commands_count))
                    end
                end
            end
        end
    end
    log('SUMMARY', 'arsenals=' .. tostring(arsenal_count) .. '|attacks=' .. tostring(attack_count) .. '|populated=' .. tostring(populated))
end
return {}
