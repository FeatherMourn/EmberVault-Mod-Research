# Troubleshooting guide

Start with Control Center health, current errors, historical errors, the last
successful session, and the compatibility report. If the loader reports a
missing or invalid module, stop the game, quarantine that module, restore the
last-known-good profile, and rescan. Keep the exact log and build identity when
reporting a new failure.

## Guided recovery

Open **Troubleshooter** and choose **Run full check** first. The report includes
game/runtime state, active profile, loader modules, installed-mod integrity,
compatibility, content validation, backup integrity, and logs.

If the runtime has failed, use **Runtime crashed** only after Enshrouded is
closed. Control Center will automatically quarantine a single identifiable
failing mod and record a reversible recovery point. If it cannot identify one
safe candidate, it stops and asks for review instead of changing files.

Do not repeat a failed research mutation until the quarantined module and the
last-known-good profile have been reviewed.
