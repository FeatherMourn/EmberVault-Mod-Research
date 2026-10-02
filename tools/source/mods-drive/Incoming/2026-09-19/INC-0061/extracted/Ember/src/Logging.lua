-- ========================================
--                LOGGING
-- ========================================

function _emit(lines)
    if not lines or #lines == 0 then return end
    for i = 1, #lines do
        print("[EMBER] " .. tostring(lines[i]))
    end
end

_feature = nil

function feature_begin(title, level)
    level = level or 1
    if LOG_LEVEL < level then
        _feature = { muted = true, level = level }
        return
    end
    _feature = {
        muted = false,
        level = level,
        title = tostring(title),
        lines = {}
    }
end

function feature_end(didWork)
    local f = _feature
    _feature = nil
    if not f or f.muted then return end
    if not didWork then return end

    _emit({ "▾▾▾ " .. f.title .. " ▾▾▾" })
    _emit(f.lines)
    _emit({ "▴▴▴ " .. f.title .. " ▴▴▴" })
end

function log_line(msg, level)
    level = level or 1
    if LOG_LEVEL < level then return end

    if _feature and not _feature.muted then
        _feature.lines[#_feature.lines + 1] = tostring(msg)
        return
    end
    _emit({ tostring(msg) })
end

function log_block(lines, level)
    level = level or 1
    if LOG_LEVEL < level then return end
    if not lines or #lines == 0 then return end

    if _feature and not _feature.muted then
        for i = 1, #lines do
            _feature.lines[#_feature.lines + 1] = tostring(lines[i])
        end
        return
    end
    _emit(lines)
end

function log_kv(prefix, t, level)
    level = level or 1
    if LOG_LEVEL < level then return end

    local parts = {}
    for k, v in pairs(t) do
        parts[#parts + 1] = ("%s=%s"):format(tostring(k), tostring(v))
    end
    log_line(prefix .. " " .. table.concat(parts, " "), level)
end
