-- ========================================
--              BUFF TWEAKS
-- ========================================
local function BuffReapplication()
    feature_begin("Buff Reapplication", 1)

    if not Enable_BuffReapplication then
        feature_end(false)
        return
    end

    local buffTypes = game.assets.get_resources_by_type("keen::BuffType")
    if not buffTypes or #buffTypes == 0 then
        feature_end(false)
        return
    end

    local changed = 0
    local scanned = 0

    local shown = 0
    local SHOW_LIMIT = 20

    for _, b in ipairs(buffTypes) do
        scanned = scanned + 1
        local d = b and b.data
        if d and d.applyType == "ReplaceAtEnd" then
            d.applyType = "Replace"
            changed = changed + 1

            if LOG_LEVEL >= 2 and shown < SHOW_LIMIT then
                shown = shown + 1
                log_line(("  buff[%d] guid=%s applyType: ReplaceAtEnd -> Replace"):format(
                    shown, tostring(b.guid or "nil")
                ), 2)
            end
        end
    end

    if changed > 0 then
        log_line(("  BuffType scanned=%d changed=%d"):format(scanned, changed), 1)
        if LOG_LEVEL >= 2 and changed > SHOW_LIMIT then
            log_line("  (Display list truncated, increase SHOW_LIMIT to print all)", 2)
        end
    end

    feature_end(changed > 0)
end

return BuffReapplication
