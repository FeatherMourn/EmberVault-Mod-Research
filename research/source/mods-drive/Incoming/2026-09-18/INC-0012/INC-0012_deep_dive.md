# Architect Toolkit — Second Deep Dive (INC-0012 working review)

Date: 2026-09-18 (America/Los_Angeles)
Reviewed user upload observed SHA-256: `9817c6919c0d634507221ecd73530af817cb3a8da13674f1ddd12fcd55ce3c0d`
Comparison baseline: prior INC-0011 source snapshot (SHA-256 `9bf199749f3001cfdf2c108d03bc1c46b0953e712b06e112cf0eb0645b16c6a8`)

## Executive result

The new changes fix several real defects from INC-0011, especially startup injection, AOB uniqueness/bounds, full F7 parameter preservation, patch readback, and F8 rejection feedback. However, the package still has several high-impact integration defects. The most important are:

1. `carrier.equip_shape` falsely reports success for <=64 voxels without changing the live carrier resource or invoking a proven refresh path.
2. The cheat-correlation item hook and the existing Inventory Move observer both own RVA `0x388453`; current initialization gives the cheat harness first chance to overwrite it, so the inventory observer can no longer validate/install.
3. F7 still treats successful publication of a JSON command as successful execution. After current UI-to-native mappings, 48 of 69 literal F7 `Send-CheatCommand` action names still resolve to action strings the native parser does not accept. The bundled `ai.kill_radius` command plus native rejection log is direct evidence.
4. `NativeMemoryEngine` still attaches with write access and starts its scanner/sweeper without enforcing the exact-build SHA that the DLL injector enforces. The launcher explicitly continues after injector/build-gate failure.
5. Two independent mutation engines (external C# process memory patches and injected native C patches/hooks) can operate on the same features, creating patch ownership and restore-order conflicts.
6. Cheat hook installation results are ignored; the harness marks itself ACTIVE / `lastFailure=NONE` even when individual hooks fail. Toggle flags such as god mode can therefore say ON while their required hook is absent.
7. Persistent `command.json` is still not consumed/deleted and `lastCommandId` is memory-only, so stale commands replay after executor restart.
8. Teleport still parses signed fixed-point coordinates with `json_get_u64`; negative coordinates fail.

The package should be repaired at these boundaries rather than rewritten wholesale. Pure/offline subsystems remain healthy in this review environment.

## Exact source delta vs INC-0011

Only three substantive source files changed:

- `runtime/ArchitectRuntime.ps1`
- `runtime/NativeMemoryEngine.cs`
- `runtime/WaitAndInject.ps1`

Bridge runtime evidence also changed (`bridge/cheat_correlation_command.json`, `bridge/executor_ack.json`) and Python cache files were added/changed. No other source file changed.

## Confirmed fixes

### FIXED — launcher now invokes native injector

`runtime/WaitAndInject.ps1:25-37` calls `ArchitectInjector.ps1` before launching the PowerShell runtime.

The bundled `bridge/native_status.json` is strong runtime evidence that injection worked in at least the captured session:

- version `0.39.0`
- build ID `architect-v039-cheat-correlation-code0033-20260917-a`
- `loadedInsideGame=true`
- `buildFingerprintValidated=true`
- `buildingPlaceSignatureMatchCount=1`

### FIXED — AOB scanner now fails closed on ambiguity

`runtime/NativeMemoryEngine.cs:623-699` now:

- validates non-null module base;
- bounds scanning to the actual module span;
- caps each memory region to module end;
- returns zero immediately on a second match;
- returns a target only for exactly one match.

This corrects the prior false-uniqueness and over-scan defects.

### FIXED / IMPROVED — external patch writes verify readback

`NativeMemoryEngine.ApplyPatch` and `RevertPatch` now validate full read/write sizes and verify bytes after mutation/restoration.

### FIXED — full F7 parameter object preserved

`ArchitectRuntime.ps1:1135-1163` now stores `parameters` and also flattens all parameter properties into the native envelope. This fixes the previous loss of fields other than phase/value/x/y/z.

### IMPROVED — F8 UI waits for matching ACK

The F8 Equip handler now processes/waits for a matching executor ACK and displays blocked/queued states rather than always displaying success.

### IMPROVED — oversized carrier geometry fails closed

Current captured `executor_ack.json` correctly rejects the 824-voxel Spiral Stairs as `unsupported_capacity` instead of pretending the command is supported.

## Critical / high findings

### CRITICAL — <=64-voxel F8 equip is still a false success

`ArchitectRuntime.ps1:1500-1520` handles `carrier.equip_shape` for <=64 voxels by writing `single_placement_carrier_status.json` and an executor success ACK. It never consumes `payloadHex`, modifies the Lua carrier resource, invokes the carrier live-refresh probe, or calls a proven game resource-refresh boundary.

The Lua layer still explicitly declares:

- `liveShapeSwapSupported = false`
- `selectionRequiresRestart = true`
- live in-session swapping is not enabled.

Canonical project state likewise says live in-session/F8 carrier refresh is UNSOLVED. Therefore “Carrier shape equipped to wand” is not supported by an execution path in this snapshot.

Recommended correction: return `unsupported_live_refresh` for every live equip until a bounded refresh/readback path is proven. Do not expose success merely because the geometry fits 64 voxels.

### CRITICAL — cheat item hook collides with existing Inventory Move observer

Two different hooks target the same instruction at RVA `0x388453`:

- `CheatCorrelationHarness.c:227` installs `CC_ITEM_SIG` / `architect_cheat_item_entry` at `g_imageBase + 0x388453`.
- `ArchitectNativeRuntime.c:2861-2879` installs the existing Inventory Move probe at `SEMANTIC_INVENTORY_MOVE_HOOK_RVA`, which `SemanticActionBuildProfile.h` defines as `0x388453` with a 12-byte overwrite.

Initialization order is also explicit:

- `ArchitectNativeRuntime.c:4450` calls `cheat_correlation_initialize(...)` first.
- `ArchitectNativeRuntime.c:4459` attempts `install_inventory_move_probe()` afterward.

Because both require the original bytes, only one can own that site. The bundled native log contains older successful `InventoryMovePointerProbe installed...` entries followed by repeated current `InventoryMovePointerProbe NOT installed; build/signature validation failed closed.` entries.

Recommended correction: do not install two independent trampolines at one RVA. Use one hook owner and fan out observations internally, or remove the cheat item hook until it can compose with the existing observer.

### CRITICAL — exact-build gate can be bypassed by NativeMemoryEngine

`ArchitectInjector.ps1` correctly refuses injection if `enshrouded.exe` SHA-256 differs from `af2f5a1227911d8aa06b3908d6bd0211838211cae14ea91099cb57d0df990781`.

But `ArchitectRuntime.ps1:758-779` calculates the process executable SHA and then calls `NativeMemoryEngine.Attach(pid)` without comparing it to the expected build. `NativeMemoryEngine.Attach` opens the process with write/operation access, registers patches, enables the scanner, and starts the memory sweeper automatically.

Worse, `WaitAndInject.ps1:33-36` catches injector failure and says it is proceeding with the in-process memory scanner/bridge, then still prints the READY banner.

Recommended correction: make a single exact-build capability gate authoritative. If the DLL injector rejects the game build, the C# memory engine must remain read-disabled/write-disabled and the UI must show incompatible build.

### HIGH — F7 publication still equals false “completed” execution

`ArchitectRuntime.ps1:1164-1167` returns `accepted=true`, `state="completed"`, `message="Cheat command queued successfully."` immediately after writing `cheat_correlation_command.json`. It never waits for native acceptance/readback.

Static command-contract audit found 69 literal `Send-CheatCommand` UI action names. After applying the current PowerShell mappings, 48 resolve to action strings not recognized by `parse_cheat_correlation_command`.

Examples include:

- `ai.kill_radius`
- `ai.disable_aggro`
- `camera.fov`
- `camera.freecam`
- `movement.gravity`
- `movement.hover` -> mapped to unsupported `glider.flying`
- `glider.speed_mul`
- `glider.lift_mul`
- `player.attributes.set`
- `player.recovery.set`
- `player.scaling.set`
- `world.time_pause`
- many inventory, entity, progression, terrain, prop and game-settings actions.

Direct bundled evidence: `bridge/cheat_correlation_command.json` contains `action: "ai.kill_radius"`; `native_runtime.log` contains `CheatCorrelation command rejected fail closed.`

Recommended correction: add a native command ACK with commandId/action/result and make F7 success depend on that ACK plus readback when mutation is involved. Capability-gate unsupported actions in the UI.

### HIGH — semantic mismatch: “fill” actions toggle permanent cheats

PowerShell maps:

- `player.health.fill` -> `cheat.godmode.toggle`
- `player.mana.fill` -> `cheat.mana.toggle`
- `player.stamina.fill` -> `cheat.stamina.toggle`

Those are not equivalent user operations. A one-shot refill should not toggle an infinite-resource mode.

Recommended correction: disable the fill buttons until a proven one-shot write/action exists, or relabel them as the actual toggle operation.

### HIGH — duplicate mutation ownership across C# and injected native runtime

`Send-CheatCommand` often performs a C# `NativeMemoryEngine` mutation first, then publishes a native mutation for the same feature. This occurs for shroud, durability, fall damage, oxygen, cold, free craft, parry, glider stamina, and altar controls, among others.

This creates two independent patch owners with different original-byte buffers and lifecycle. If one engine sees bytes already patched by the other, its restore state can be wrong.

Concrete related C# defect: `ApplyPatch` treats “already patched” as success after copying the current patched bytes into `originalBytes`; the caller then stores those patch bytes as the supposed original. A later Disable writes the patch bytes back and marks the patch inactive.

Recommended correction: exactly one backend owns each mutation target. The other layer may request it but must not independently patch it.

### HIGH — cheat hook initialization claims ACTIVE even when hooks failed

`CheatCorrelationHarness.c:218-228` invokes ten `cc_install_one()` hooks but discards every return value. Then at lines 270-274 it unconditionally sets:

- `active = TRUE`
- `lastFailure = "NONE"`
- phase `ACTIVE`

Actions such as god mode/mana/stamina also simply toggle flags and return success without proving the required hook exists.

Recommended correction: track installation state per hook. An action requiring a hook must reject if that hook is absent. Overall ACTIVE should mean the required hook set actually passed validation and installation.

### HIGH — native byte patches lack an expected-byte precondition

`CheatCorrelationHarness.c:152-159` `patch_bytes()` copies whatever bytes are currently present and overwrites them. It does not compare current bytes to a build-profile expected instruction sequence before mutation.

Exact build fingerprinting reduces update risk, but this still conflicts with another mod/Architect mutation that has already changed the same location. It can capture another patch as “original.”

Recommended correction: store expected-original bytes for each patch target and require an exact match before first enable. Treat “already patched by this same owner” separately from “unexpected bytes.”

### HIGH — stale command replay remains

`command.json` is persistent. `lastCommandId` is initialized to null each PowerShell process and is only stored in memory. `Process-ArchitectCommand` never consumes, moves, or deletes `command.json`.

Therefore a restart can process the previous command again. With current false-success carrier handling this can also generate a fresh misleading success ACK for an old request.

Recommended correction: atomically rename a command to a processing file, persist consumed IDs or archive/delete after terminal ACK, and make executor restarts idempotent.

### HIGH — mutation/evidence state is contradictory

The injected runtime reports mode `observe_only_cheat_correlation` and native status reports `targetGameMutation=false`, while its command parser implements executable mutation toggles/patches.

Canonical Project Control currently records no safe live mutation target / mutation gate disabled and CODE-0033 as observe-only correlation. The current package therefore enables behavior beyond its evidence state and diagnostics language.

Recommended correction: either keep CODE-0033 truly observe-only, or create a separate explicitly approved mutation build after each target has owner/readback/revert proof. Do not use observe-only identity/status for a mutation-capable runtime.

## Other confirmed defects

### Teleport rejects negative coordinates

Native `cheat.teleport` parses x/y/z with `json_get_u64`. `json_get_u64` accepts digits only and rejects a leading `-`. PowerShell serializes signed coordinates. Any negative coordinate component therefore causes the native teleport command to fail parsing.

### Several C# “settings” are only local variables

`SetPlayerAttribute`, `SetWeaponScaling`, `SetRecoveryMultipliers`, and `SetGliderMultipliers` only update C# state. They do not have a proven Enshrouded write path in these functions.

`SetSpeedMultiplier` and `SetWorldGravity` write only if `CapturedPlayerTransform` is nonzero; the C# layer has no active position hook in this snapshot to establish that pointer. Native capture is a separate runtime and does not automatically populate the C# static pointer.

### Dual `command.json` schemas remain

The native general command parser requires `id`, `action`, `backendKey`, and `backendItemId`. New F8 carrier commands use `commandId`, `action`, and `parameters`. PowerShell can intercept the latter, but two incompatible consumers still share one filename/protocol surface.

Recommended correction: one versioned envelope and one dispatcher boundary.

### Launcher still announces READY after native injection failure

Even a build mismatch or failed injection falls through to the READY banner. Readiness should be capability-specific and derived from verified runtime state.

## Offline test results in this review environment

Passed:

- Structure Recorder: 11 tests
- Structure Editor: 8 tests
- Semantic Capture Analyzer: 11 tests
- Architect Core: 5 tests
- Player Observer: 14 tests
- Player Discovery: 9 tests
- Cheat Correlation: 14 tests
- Camera FOV: 8 tests
- ArchitectVoxel: 7 tests when invoked with its expected module path

The monolithic offline regression cannot complete here because it expects a local `enshrouded.exe`; PowerShell/C# compilation cannot be independently run because this analysis container has no `powershell`/`pwsh` or C# compiler. Those are environment limits, not test failures attributable to the source.

## Recommended NEXT BUILD order

1. **Resolve hook ownership collision at `0x388453`.** Preserve the established Inventory Move observer; compose cheat item capture through the same trampoline or disable the new item hook.
2. **Restore fail-closed build gating.** No C# write/scanner/sweeper on an unsupported executable SHA; no READY state after build-gate failure.
3. **Make one mutation backend authoritative per capability.** Do not patch the same feature in C# and native C.
4. **Add native command ACK/readback.** Do not treat JSON publication as execution.
5. **Disable the 48 UI actions without a recognized/proven backend.** Re-enable individually as evidence arrives.
6. **Change F8 <=64 equip to UNSOLVED/unsupported until live carrier refresh is actually implemented and verified.** Keep restart/config carrier switching as the proven path.
7. **Track every hook install result and gate dependent toggles on it.**
8. **Consume commands atomically and persist terminal execution identity to prevent replay.**
9. **Fix signed teleport serialization/parser.**
10. Only then resume adding cheat/action coverage.

## Bottom line

The edits fix several important low-level defects, especially injection and AOB safety. The present blocker is architectural integration: command/UI capability claims and mutation ownership still exceed what the backend has actually validated. The highest-value next change is not adding more actions; it is making one fail-closed command/capability/mutation path authoritative and removing collisions/false success.
