local UPDRAFT_GUID = "56f35356-aa4b-4cc1-b5c6-088ecce9aa45"
local TARGET_TYPE  = "keen::actor::ActorSequenceResource"

-- ========================================
--            CALCULATION HELPER
-- ========================================

local function normalize_duration_ns(v)
  if v == nil then return nil end
  if type(v) ~= "number" then
    log_line("WARN: Boost_Duration must be a number or nil; got " .. type(v), 1)
    return nil
  end

  if v < 1000 then
    return math.floor(v * 1000000000 + 0.5)
  end

  return math.floor(v + 0.5)
end

local function patch_scalar_if(obj, field, new_val, context)
  if new_val == nil then return end
  if not obj then return end
  if obj[field] ~= new_val then
    log_line(string.format("%s %s: %s -> %s", context, field, tostring(obj[field]), tostring(new_val)), 2)
    obj[field] = new_val
    return true
  end
end

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
  local ok, iter, state, init = pcall(function() return ipairs(arr) end)
  if not ok then return false end
  for i, v in iter, state, init do
    fn(i, v)
  end
  return true
end

local function apply_ignore_mana_cost(val, context)
  if not val then return false end

  local mask = safe_get(val, "ignoreCostMask")
  local target = "Mana"

  if mask == nil then
    if safe_set(val, "ignoreCostMask", { target }) then
      log_line(context .. " ignoreCostMask: set {Mana}", 2)
      return true
    end
    log_line(context .. " ignoreCostMask: failed to set", 1)
    return false
  end

  local found = false
  iter_array(mask, function(_, v)
    if tostring(v) == target then
      found = true
    end
  end)
  if found then
    log_line(context .. " ignoreCostMask: already contains Mana", 2)
    return false
  end

  local idx = 1
  iter_array(mask, function(i) idx = i + 1 end)
  local ok, err = safe_set(mask, idx, target)
  if ok then
    log_line(context .. " ignoreCostMask: appended Mana", 2)
    return true
  end

  ok, err = safe_set(val, "ignoreCostMask", { target })
  if ok then
    log_line(context .. " ignoreCostMask: replaced with {Mana}", 2)
    return true
  end

  log_line(context .. " ignoreCostMask: update failed (" .. tostring(err) .. ")", 1)
  return false
end

local function apply_mana_cost_override(val, new_value, context)
  if not val or new_value == nil then return false end

  local impacts = safe_get(val, "impactValues")
  if not impacts then return false end

  local changed = false
  iter_array(impacts, function(i, entry)
    local entry_val = safe_get(entry, "value") or safe_get(entry, "$value")
    if entry_val then
      local old = safe_get(entry_val, "value")
      if type(old) == "number" and old ~= new_value then
        local ok = safe_set(entry_val, "value", new_value)
        if ok then
          log_line(string.format("%s impactValues[%d].value: %s -> %s", context, i, tostring(old), tostring(new_value)), 2)
          changed = true
        end
      end
    end
  end)
  return changed
end

local function patch_updraft(res)
  local data = res and res.data
  if not data or not data.subSequences then
    log_line("WARN: Invalid sequence structure (no subSequences)", 1)
    return 0
  end

  local changed = 0
  for si, seq in ipairs(data.subSequences) do
    for ei, event in ipairs(seq.events or {}) do
      local context = string.format("Seq[%d].Event[%d](%s)", si, ei, tostring(event.type))
      local val = event.value
      if not val then goto continue end

      if event.type == "keen::actor::ImpulseEvent" then
        if val.uprightImpulse then
          if patch_scalar_if(val.uprightImpulse, "x", GroundRelative_X,  context .. ".uprightImpulse.x") then changed = changed + 1 end
          if patch_scalar_if(val.uprightImpulse, "y", GroundRelative_Y,  context .. ".uprightImpulse.y") then changed = changed + 1 end
          if patch_scalar_if(val.uprightImpulse, "z", GroundRelative_Z,  context .. ".uprightImpulse.z") then changed = changed + 1 end
        end

        if val.orientedImpulse then
          if patch_scalar_if(val.orientedImpulse, "x", PlayerRelative_X, context .. ".orientedImpulse.x") then changed = changed + 1 end
          if patch_scalar_if(val.orientedImpulse, "y", PlayerRelative_Y, context .. ".orientedImpulse.y") then changed = changed + 1 end
          if patch_scalar_if(val.orientedImpulse, "z", PlayerRelative_Z, context .. ".orientedImpulse.z") then changed = changed + 1 end
        end

        if val.duration then
          if patch_scalar_if(val.duration, "value", normalize_duration_ns(Boost_Duration), context .. ".duration.value") then changed = changed + 1 end
        end
      elseif event.type == "keen::actor::PayUsageCost" then
        if Updraft_IgnoreManaCost then
          if apply_ignore_mana_cost(val, context .. ".ignoreCostMask") then changed = changed + 1 end
        end
        if Updraft_ManaCost_Value ~= nil then
          if apply_mana_cost_override(val, Updraft_ManaCost_Value, context) then changed = changed + 1 end
        end
      end

      ::continue::
    end
  end

  return changed
end

local function main()
  feature_begin("Updraft Tweaks", 1)

  if not Enable_SkillTweaks_Updraft then
    feature_end(false)
    return
  end

  local list = game.assets.get_resources_by_type(TARGET_TYPE)
  if not list or #list == 0 then
    log_line("WARN: No resources found for type: " .. TARGET_TYPE, 1)
    feature_end(false)
    return
  end

  for _, res in ipairs(list) do
    if tostring(res.guid) == UPDRAFT_GUID then
      local changed = patch_updraft(res)
      if changed > 0 then
        log_line("Updraft changes applied: " .. tostring(changed), 1)
      end
      feature_end(changed > 0)
      return
    end
  end

  log_line("WARN: Updraft ActorSequence GUID not found: " .. UPDRAFT_GUID, 1)
  feature_end(false)
end

return main
