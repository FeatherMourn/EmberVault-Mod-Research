# Architect Toolkit INC-0011 — Static/Offline Deep Dive

Date: 2026-09-18
Snapshot SHA-256: 9bf199749f3001cfdf2c108d03bc1c46b0953e712b06e112cf0eb0645b16c6a8
Status: STAGED ANALYSIS ONLY — does not designate Architect_Mod/Current and does not promote canonical runtime claims.

## Executive finding
The snapshot is not failing because one central subsystem is wholly broken. Its strongest failure pattern is runtime integration drift: the F7/F8 UI exposes actions that the active PowerShell/native backends do not support, two incompatible command-envelope generations share the same bridge file, the launcher does not invoke the native injector, and several mutation/reporting paths report success without execution proof.

## PROVEN static/runtime-capture findings

1. **F8 `carrier.equip_shape` is rejected by the PowerShell executor.**
   - Producer: `runtime/VoxelGeometryEngine.psm1:239-252` writes version 1 / `commandId` / action `carrier.equip_shape` / nested parameters.
   - Dispatcher: `runtime/ArchitectRuntime.ps1:1428-1451` accepts registered v1 admin commands or only legacy `preview` / `place`; all others reject.
   - Captured `bridge/executor_ack.json` confirms `carrier.equip_shape` => `rejected`, `Unsupported Architect action.`

2. **Two incompatible command schemas coexist in `bridge/command.json`.**
   - New shape path: `commandId`, nested `parameters` (`VoxelGeometryEngine.psm1:239-252`).
   - Legacy F8 writer: version `0.6.0`, `id`, top-level `backendKey`, `backendItemId` (`ArchitectRuntime.ps1:1663-1685`).
   - Native parser requires legacy `id`, `action`, `backendKey`, and `backendItemId` before dispatch (`ArchitectNativeRuntime.c:4094-4119`).
   - Therefore the new shape envelope cannot reach native general action handling even if a new action branch were added without adapting the schema.

3. **F8 equip UI reports success without consuming an executor acknowledgement.**
   - `ArchitectRuntime.ps1:5251-5269` writes the command and immediately displays “Equipped … Click in world to place!” / “Status: Equipped to Wand!” when only the bridge write succeeded.
   - Current bridge capture contradicts that UI message: executor ack is rejected.

4. **The requested live carrier behavior conflicts with the proven startup carrier design.**
   - `src/Config/Architect_Blueprint_Config.lua:1-6` explicitly requires full restart and states live in-session swapping is not enabled.
   - `src/mod.lua:1050-1060` requires exactly `ARCHITECT_CARRIER_VOXEL_COUNT` voxels; `1089-1102` fails closed when placement bytes exceed the safe EML bound.
   - Current captured F8 command asks for Spiral Stairs, dimensions 17x20x17, 824 occupied voxels, 723 payload bytes. It is not compatible with simply whitelisting the current startup carrier path.

5. **General live preview/placement is intentionally not executed by the current executor.**
   - `bridge/executor_status.json`: `liveExecutionEnabled=false`, reason `In-process preview/placement hook not mapped yet`.
   - PowerShell validates `preview`/`place` but describes the live hook as remaining work.
   - Native `ArchitectNativeRuntime.c:4160-4195` makes ordinary `place` trace-only and explicitly disarms mutating carrier state.

6. **The normal launcher never invokes the native injector.**
   - `runtime/WaitAndInject.ps1:25-27` starts `ArchitectRuntime.ps1`, not `ArchitectInjector.ps1`.
   - `Run Architect Runtime.bat:5-11` and `Launch Enshrouded with Architect.bat:12-14` claim automatic injection, but their path only calls WaitAndInject.
   - A clean user start can therefore open F7/F8 while the in-process native runtime is absent unless another/manual path injects it.

7. **`Launch Enshrouded with Architect.bat` does not launch Enshrouded when double-clicked with no arguments.**
   - Line 5 is only `start "" %*`. With no wrapper arguments, no game command is supplied; WaitAndInject then waits for a game process started elsewhere.

8. **The C# `ScanModuleUnique` function does not enforce uniqueness and scans beyond the module.**
   - `NativeMemoryEngine.cs:632-633`: scan span is `Math.Max(moduleSize, 0x10000000)`, so a module smaller than 256 MB causes scanning outside the main module range.
   - `:676-680`: on the second match it returns the first match instead of failing ambiguity.
   - `:695`: any single-or-more match returns the first.
   - `ResolveAll:715-720` marks that result resolved.
   - `Attach:398-412` opens write-capable access and starts scanning automatically.

9. **The C# scanner attaches before the PowerShell layer enforces a game build hash.**
   - `ArchitectRuntime.ps1:758-776` computes `attachedSha256` but immediately calls `[NativeMemoryEngine]::Attach` without comparing the hash to an expected build fingerprint in this path.

10. **Soft/queued memory toggles can display ON without applying a patch.**
    - `NativeMemoryEngine.cs:786-793` flips a SoftToggle for bridge feature names and reports `ENABLED (Sweep Active)` without game mutation.
    - `:812-819` reports `ENABLED (Sweep queued)` when an actual patch cannot resolve.
    - Sweeper `:444-483` only calls ResolveAll/read/autorun; it does not later apply queued soft toggles.
    - `IsPatchActive:886-890` reports the SoftToggle as active, which can make the UI appear successful.

11. **Several F7 setters only change C# local variables.**
    - `SetPlayerAttribute`, `SetWeaponScaling`, `SetRecoveryMultipliers`, and `SetGliderMultipliers` (`NativeMemoryEngine.cs:539-605`) do not write proven game state.
    - They are called by `Send-CheatCommand` and can be followed by a success-looking bridge result.

12. **The F7 cheat bridge drops most parameters and equates publication with completion.**
    - `ArchitectRuntime.ps1:1111-1135` only serializes `phase`, `value`, `x`, `y`, `z` from `Command.parameters`; all other parameter keys are discarded.
    - It returns state `completed` with message `Cheat command queued successfully.` after only writing the file.
    - `Send-CheatCommand:1140-1254` also swallows direct execution exceptions with an empty catch.

13. **Teleport bridge parsing rejects negative coordinates.**
    - PowerShell sends signed `[long]` fixed-point x/y/z (`ArchitectRuntime.ps1:1095-1107`).
    - Native `json_get_u64` (`ArchitectNativeRuntime.c:1445-1473`) parses digits only and has no leading-sign support.
    - `cheat.teleport` (`:1219-1225`) uses that unsigned parser for x/y/z, so any negative coordinate fails parsing.

14. **Player position falls back to fabricated coordinates instead of failing closed.**
    - `ArchitectRuntime.ps1:1058-1084` falls back to `{ X = 2410.0; Y = 150.0; Z = -1205.0 }` when runtime sources fail.
    - `NativeMemoryEngine.cs:976-979` leaves `EnsurePositionHook()` empty, increasing the chance that the C# path does not supply a live player transform.

15. **Native cheat-correlation startup ignores individual hook installation failures.**
    - `CheatCorrelationHarness.c:218-228` calls ten `cc_install_one(...)` operations but discards every return value.
    - `:270-274` then unconditionally sets the harness active and `lastFailure = NONE`.
    - A missing required hook can therefore coexist with globally “active” status.

16. **F8 protocol declarations are not contract-tested against the actual runtime dispatcher.**
    - `docs/F8_BACKEND_PROTOCOL.md` and `tools/ArchitectVoxel/f8_protocol.py:38-60` mark generic `cancel` supported.
    - `Process-ArchitectCommand` accepts only `preview` and `place` outside the admin registry; generic `cancel` is rejected.

17. **Current status/capability files contradict the mutation-heavy bespoke F7 surface.**
    - `bridge/native_status.json` says native version 0.39.0, mode `observe_only_cheat_correlation`, `targetGameMutation=false`, scope `none_observe_only`.
    - `bridge/backend_capabilities.json` says `mutationMasterGate=false`, no registered/readable/writable native-memory targets, runtime mutation NOT_PROVEN.
    - Meanwhile the bespoke F7 path bypasses the registry with `Send-CheatCommand` and direct `NativeMemoryEngine` calls. This is an architecture/state-reporting split and makes capability-gating unreliable.

18. **Persistent command files replay stale work after a runtime restart.**
    - PowerShell only remembers `lastCommandId` in process memory and does not consume/archive `command.json` after acknowledgement.
    - Current executor logs show the same stale `carrier.equip_shape` command being rejected again on subsequent executor starts.

## Offline test result summary
Most pure Python suites that do not require Windows/game artifacts passed (ArchitectVoxel, StructureRecorder, StructureEditor, SemanticCaptureAnalyzer, ArchitectCore, PlayerObserver, CameraFov, CheatCorrelation, PlayerDiscovery; CheatSprint had two passes and one skip). Full regression was not reproducible in the analysis sandbox because `/mnt/data/enshrouded.exe`, PowerShell, and some optional Python RE packages (`capstone`, `pefile`) were absent. These are environment/tooling limitations, not evidence that those product subsystems fail in-game.

## Recommended repair order
1. Capability-gate F7/F8 UI and stop reporting success before a matching execution ack/readback.
2. Choose one versioned bridge command schema and one authoritative dispatcher; add parity/contract tests.
3. Wire `ArchitectInjector.ps1` into the launcher with verified version/build handshake before declaring READY.
4. Make bridge commands single-use/transactional (atomic inbox -> processing -> ack -> archive) to prevent replay.
5. Fix `ScanModuleUnique`: exact module/section bounds, return zero on ambiguity, exact-build gate before scanner, expected-byte validation before any patch.
6. Remove fake SoftToggle success states; unsupported/unresolved actions must remain visibly unavailable.
7. Make player position fail unavailable instead of using hardcoded coordinates; add signed integer JSON parsing for teleport.
8. Keep live carrier swapping disabled until a bounded resource-refresh mechanism is independently proven. Do not make `carrier.equip_shape` functional by merely whitelisting 824-voxel payloads.

