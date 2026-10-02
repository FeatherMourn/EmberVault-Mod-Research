-- ==================================================
--                 SPELL TWEAKS
-- ==================================================
local MANA_IMPACT_TYPE_ID = 2556031774
local RANGED_COMBAT_IMPACT_TYPE_ID = 3902764048
local SPELL_CHARGE_DURATION_CONFIG_ID = 1469785687
local SPELL_CHARGE_DURATION_LOCA_TAG = "749b51e4-7f06-4064-98f1-fe22b7b3e08d"
local ACTOR_SEQUENCE_RESOURCE_TYPE = "keen::actor::ActorSequenceResource"
local PAY_USAGE_COST_TYPE = "keen::actor::PayUsageCost"

local function safe_get(obj, field)
    local ok, val = pcall(function() return obj[field] end)
    if ok then return val end
    return nil
end

local function safe_set(obj, field, value)
    local ok, err = pcall(function() obj[field] = value end)
    if ok then return true end
    return false, err
end

local function iter_array(arr, fn)
    if not arr then return end
    local ok, iter, state, init = pcall(function() return ipairs(arr) end)
    if not ok then return end
    for i, value in iter, state, init do
        fn(i, value)
    end
end

local function round_scaled(value, multiplier)
    local scaled = value * multiplier
    if scaled >= 0 then
        return math.floor(scaled + 0.5)
    end
    return -math.floor((-scaled) + 0.5)
end

local function approx_equal(a, b, tolerance)
    return math.abs(a - b) <= tolerance
end

local function is_spell_ammunition(data)
    local debugName = tostring(data and data.debugName or "")

    return data
        and tostring(data.category or "") == "Ammunition"
        and tostring(data.ammunitionType or "") == "Spell"
        and (
            debugName:match("^Ammo_T%d+_Spell") ~= nil
            or debugName:match("^Ammo_Magic_Staff_") ~= nil
        )
end

local function get_entry_value(entry)
    return safe_get(entry, "value") or safe_get(entry, "$value")
end

local function collect_sequence_guids(itemData, sequenceGuids)
    iter_array(itemData and itemData.sequences, function(_, sequenceInfo)
        local sequenceGuid = sequenceInfo and safe_get(sequenceInfo, "sequence")
        if sequenceGuid then
            sequenceGuids[tostring(sequenceGuid)] = true
        end
    end)
end

local function patch_mana_impacts(itemData, manaMult)
    local impacts = itemData and itemData.impactValues
    if not impacts then
        return 0, {}
    end

    local changed = 0
    local originalManaValues = {}

    for _, bucketName in ipairs({ "simple", "scaled" }) do
        iter_array(impacts[bucketName], function(_, entry)
            local entryValue = get_entry_value(entry)
            local impactType = entryValue and entryValue.type
            local impactTypeValue = impactType and impactType.value

            if impactTypeValue == MANA_IMPACT_TYPE_ID then
                local old = entryValue.value
                if type(old) == "number" and old > 0 then
                    originalManaValues[tostring(old)] = true

                    local new = round_scaled(old, manaMult)
                    if new ~= old then
                        entryValue.value = new
                        changed = changed + 1
                    end
                end
            end
        end)
    end

    return changed, originalManaValues
end

local function patch_mana_ui_values(itemData, originalManaValues, manaMult)
    local uiValues = itemData and itemData.uiValues
    if not uiValues then
        return 0
    end

    local changed = 0
    iter_array(uiValues, function(_, entry)
        local old = entry and entry.value
        if type(old) == "number" and originalManaValues[tostring(old)] then
            local new = round_scaled(old, manaMult)
            if new ~= old then
                entry.value = new
                changed = changed + 1
            end
        end
    end)

    return changed
end

local function is_spell_charge_duration_entry(entryValue)
    if not entryValue then return false end

    local impactType = entryValue.type
    local impactTypeValue = impactType and impactType.value
    return impactTypeValue == RANGED_COMBAT_IMPACT_TYPE_ID
        and entryValue.configId
        and entryValue.configId.value == SPELL_CHARGE_DURATION_CONFIG_ID
        and tostring(entryValue.valueFormat or "") == "Duration"
        and tostring(entryValue.locaTag or "") == SPELL_CHARGE_DURATION_LOCA_TAG
end

local function patch_charge_duration_impacts(itemData, castMult)
    local impacts = itemData and itemData.impactValues
    if not impacts then
        return 0, {}
    end

    local changed = 0
    local uiTargets = {}

    for _, bucketName in ipairs({ "simple", "scaled" }) do
        iter_array(impacts[bucketName], function(_, entry)
            local entryValue = get_entry_value(entry)
            if not is_spell_charge_duration_entry(entryValue) then
                return
            end

            local old = entryValue.value
            if type(old) == "number" and old > 0 then
                uiTargets[#uiTargets + 1] = {
                    oldMs = round_scaled(old * 1000, 1.0),
                    newMs = round_scaled(old * 1000, castMult)
                }

                local new = old * castMult
                if new ~= old then
                    entryValue.value = new
                    changed = changed + 1
                end
            end
        end)
    end

    return changed, uiTargets
end

local function patch_charge_duration_ui_values(itemData, uiTargets)
    local uiValues = itemData and itemData.uiValues
    if not uiValues or #uiTargets == 0 then
        return 0
    end

    local changed = 0
    iter_array(uiValues, function(_, entry)
        local old = entry and entry.value
        if type(old) ~= "number" or old <= 0 or tostring(entry.valueFormat or "") ~= "Duration" then
            return
        end

        for _, target in ipairs(uiTargets) do
            if approx_equal(old, target.oldMs, 2) then
                if old ~= target.newMs then
                    entry.value = target.newMs
                    changed = changed + 1
                end
                return
            end
        end
    end)

    return changed
end

local function apply_ignore_mana_cost(val)
    if not val then return false end

    local mask = safe_get(val, "ignoreCostMask")
    local target = "Mana"

    if mask == nil then
        return safe_set(val, "ignoreCostMask", { target })
    end

    local found = false
    iter_array(mask, function(_, v)
        if tostring(v) == target then
            found = true
        end
    end)
    if found then
        return false
    end

    local idx = 1
    iter_array(mask, function(i) idx = i + 1 end)
    local ok = safe_set(mask, idx, target)
    if ok then
        return true
    end

    return safe_set(val, "ignoreCostMask", { target })
end

local function patch_sequence_mana_free(sequenceGuids)
    local sequences = game.assets.get_resources_by_type(ACTOR_SEQUENCE_RESOURCE_TYPE)
    if not sequences or #sequences == 0 then
        log_line("WARN: No ActorSequenceResource entries found", 1)
        return 0, 0, 0, 0
    end

    local scanned = 0
    local matched = 0
    local failed = 0
    local changed = 0

    for _, sequence in ipairs(sequences) do
        scanned = scanned + 1

        local sequenceGuid = tostring(sequence and sequence.guid or "")
        if sequenceGuids[sequenceGuid] then
            matched = matched + 1

            local ok, err = pcall(function()
                local data = sequence and sequence.data
                iter_array(data and data.subSequences, function(_, subSequence)
                    iter_array(subSequence and subSequence.events, function(_, event)
                        local eventType = safe_get(event, "type") or safe_get(event, "$type")
                        if eventType ~= PAY_USAGE_COST_TYPE then
                            return
                        end

                        local val = safe_get(event, "value") or safe_get(event, "$value")
                        if apply_ignore_mana_cost(val) then
                            changed = changed + 1
                        end
                    end)
                end)
            end)

            if not ok then
                failed = failed + 1
                if LOG_LEVEL >= 2 then
                    log_line("WARN: Spell sequence tweak failed guid=" .. sequenceGuid .. " err=" .. tostring(err), 2)
                end
            end
        end
    end

    return scanned, matched, changed, failed
end

local function table_count(t)
    local count = 0
    for _ in pairs(t) do
        count = count + 1
    end
    return count
end

local function ApplySpellTweaks()
    feature_begin("Spell Tweaks", 1)

    if not Enable_SpellTweaks then
        feature_end(false)
        return
    end

    local castMult = SpellCastTime_Multiplier
    local manaMult = SpellManaCost_Multiplier

    if type(castMult) ~= "number" then
        log_line("WARN: SpellCastTime_Multiplier invalid; skipping: " .. tostring(castMult), 1)
        feature_end(false)
        return
    end
    if type(manaMult) ~= "number" then
        log_line("WARN: SpellManaCost_Multiplier invalid; skipping: " .. tostring(manaMult), 1)
        feature_end(false)
        return
    end

    local minMult = SpellTweaks_MinMultiplier
    if type(minMult) == "number" then
        if castMult < minMult then
            log_line(("WARN: SpellCastTime_Multiplier (%s) < min (%s); clamping"):format(tostring(castMult), tostring(minMult)), 1)
            castMult = minMult
        end
        if manaMult < minMult then
            log_line(("WARN: SpellManaCost_Multiplier (%s) < min (%s); clamping"):format(tostring(manaMult), tostring(minMult)), 1)
            manaMult = minMult
        end
    end

    local items = game.assets.get_resources_by_type("keen::ItemInfo")
    if not items or #items == 0 then
        log_line("WARN: No ItemInfo entries found", 1)
        feature_end(false)
        return
    end

    local scanned = 0
    local matched = 0
    local failed = 0
    local manaImpactChanged = 0
    local manaUiChanged = 0
    local chargeImpactChanged = 0
    local chargeUiChanged = 0
    local sequenceGuids = {}
    local shown = 0
    local SHOW_LIMIT = 25

    for _, item in ipairs(items) do
        scanned = scanned + 1

        local ok, err = pcall(function()
            local data = item and item.data
            if not is_spell_ammunition(data) then
                return
            end

            matched = matched + 1
            collect_sequence_guids(data, sequenceGuids)

            local itemManaChanged, originalManaValues = patch_mana_impacts(data, manaMult)
            if itemManaChanged > 0 then
                manaImpactChanged = manaImpactChanged + itemManaChanged
                manaUiChanged = manaUiChanged + patch_mana_ui_values(data, originalManaValues, manaMult)
            end

            local itemChargeChanged, chargeUiTargets = patch_charge_duration_impacts(data, castMult)
            if itemChargeChanged > 0 then
                chargeImpactChanged = chargeImpactChanged + itemChargeChanged
                chargeUiChanged = chargeUiChanged + patch_charge_duration_ui_values(data, chargeUiTargets)
            end

            if LOG_LEVEL >= 2 and shown < SHOW_LIMIT then
                shown = shown + 1
                log_line(("spell[%d] debugName=%s manaImpacts=%d chargeImpacts=%d"):format(
                    shown, tostring(data.debugName or ""), itemManaChanged, itemChargeChanged
                ), 2)
            end
        end)

        if not ok then
            failed = failed + 1
            if LOG_LEVEL >= 2 then
                log_line("WARN: Spell tweak failed guid=" .. tostring(item and item.guid or "nil") .. " err=" .. tostring(err), 2)
            end
        end
    end

    local sequenceScanned = 0
    local sequenceMatched = 0
    local sequenceManaMaskChanged = 0
    local sequenceFailed = 0
    if manaMult <= 0 then
        sequenceScanned, sequenceMatched, sequenceManaMaskChanged, sequenceFailed = patch_sequence_mana_free(sequenceGuids)
    end

    log_line(("ItemInfo scanned=%d matchedSpellAmmo=%d failed=%d"):format(scanned, matched, failed), 1)
    log_line(("Mana cost: impactValues=%d uiValues=%d manaMult=%s"):format(
        manaImpactChanged, manaUiChanged, tostring(manaMult)
    ), 1)
    if manaMult <= 0 then
        log_line(("Mana free mode: sequencesScanned=%d matched=%d ignoreManaCost=%d failed=%d"):format(
            sequenceScanned, sequenceMatched, sequenceManaMaskChanged, sequenceFailed
        ), 1)
    end
    log_line(("Charge time: impactValues=%d uiValues=%d castMult=%s sequencesReferenced=%d"):format(
        chargeImpactChanged, chargeUiChanged, tostring(castMult), table_count(sequenceGuids)
    ), 1)

    if LOG_LEVEL >= 2 and matched > SHOW_LIMIT then
        log_line("(Display list truncated, increase SHOW_LIMIT to print all)", 2)
    end

    feature_end((manaImpactChanged + manaUiChanged + sequenceManaMaskChanged + chargeImpactChanged + chargeUiChanged) > 0)
end

return ApplySpellTweaks
