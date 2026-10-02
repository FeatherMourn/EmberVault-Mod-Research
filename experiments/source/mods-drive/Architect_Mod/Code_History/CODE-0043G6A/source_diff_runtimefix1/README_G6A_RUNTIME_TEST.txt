ARCHITECT TOOLKIT CODE-0043G6A RUNTIME-FIX1 TEST

1. Completely close Enshrouded.
2. Extract this ZIP into the folder containing enshrouded.exe.
3. Run PREPARE_G6A_RUNTIME_TEST.bat before starting Enshrouded.
4. Start Enshrouded normally through Steam.
5. Load a disposable/test world or noncritical character.
6. Double-click START_ARCHITECT_G6A_TEST.bat.
7. Press F7 and open Developer & Diagnostics.
8. Click BEGIN CORRELATION.
9. Perform the sequence below.
10. Click END CAPTURE, refresh STATUS, verify correlation is inactive, and exit normally.
11. Return these fresh files from mods\architect_toolkit\bridge (or ZIP the five files): cheat_correlation_status.json, cheat_correlation_capture.jsonl, cheat_correlation_report.json, native_status.json, native_runtime.log.

DO NOT enable unrelated cheats or mutation features during this capture.

OBSERVATION SEQUENCE

BASELINE_IDLE: select, click MARK PHASE, stand completely still 5 seconds.
WALK: select, click MARK PHASE, walk normally 5 seconds.
SPRINT_ACTIVE: select, click MARK PHASE, sprint until stamina visibly decreases.
SPRINT_RECOVERY: select, click MARK PHASE, stop and remain idle until stamina visibly recovers.
JUMP: select, click MARK PHASE, perform several ordinary jumps.
POST_JUMP_RECOVERY: select, click MARK PHASE, remain idle/recover.

Optional discriminator phases: COMBAT_IDLE and MENU.

This is an observe-only Gate-B capture. Packaging does not establish runtime proof or authorize mutation.
