local function ApplyNoIntroVideo()
    feature_begin("No Intro Video", 1)

    if not Enable_NoIntroVideo then
        feature_end(false)
        return
    end

    local b0 = get_first_resource_by_type("keen::FbUiBundle")
    local ui = b0 and b0.data

    local didWork = false

    if ui and ui.preGame and ui.preGame.startUpSequence then
        ui.preGame.startUpSequence.logoFadeDuration.value = 0
        ui.preGame.startUpSequence.logoIdleDuration.value = 0
        ui.preGame.startUpSequence.postLogoDelay.value = 0
        ui.preGame.startUpSequence.mainMenuFadeInDuration.value = 0
        ui.preGame.startGameFadeOutDuration.value = 0
        didWork = true
        log_line("patched startup sequence timings", 1)
    else
        log_line("WARN: keen::FbUiBundle not present; skipping (ignore for servers).", 1)
    end

    feature_end(didWork)
end

return ApplyNoIntroVideo
