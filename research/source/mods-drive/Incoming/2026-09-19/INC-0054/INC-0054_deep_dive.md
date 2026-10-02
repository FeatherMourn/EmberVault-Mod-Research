# INC-0054 — Architect Toolkit Coding-Agent Update Deep Dive

Date: 2026-09-19 (user local) / 2026-09-20 UTC evidence timestamps
Game build: Enshrouded revision 1076226
User-uploaded archive SHA-256 observed before extraction: `fde5131ac1fe5930bead6d9b5f9118dc0e564c066904f07fe8a715872df65c42`
Drive Current baseline SHA-256: `a1ab3aeee18987c0f4f27cc0b49a371c89f3f82be5ec8342bd9536b86516835a`
Audit working tree: extracted from the user upload before the Drive-current comparison.

## Executive result

The coding-agent update contains real forward progress, especially the corrected resource-first QoL layer and a hardened native Free Craft direct-patch candidate. However, the package is **not currently qualified as a safe release/test baseline** because later edits reintroduced several paths that conflict with Architect's established fail-closed contracts, and the packaged `VERIFICATION_REPORT.txt` predates those later edits.

Most important classification:

- **Current runtime bootstrap / F7 shell:** runtime evidence present; loads and opens.
- **Stack size:** strong current-build KFC mapping + prior runtime execution evidence.
- **Storage expansion:** exact KFC profile validated; corrected implementation present; runtime gameplay proof still missing.
- **Auto Loot resource implementation:** target/donor profile validates against build-1076226 KFC, but current config jumps to full scope before canary proof and a second simulated-E-key Auto Loot implementation is still active.
- **Free Craft:** hardened native patch target is runtime-ready at the expected bytes; gameplay semantics remain untested.
- **Always Flying:** implementation is unqualified and bypasses the hardened native mutation model.
- **Teleport:** a previously disarmed unsafe write path has been reintroduced in source and must be disarmed again before gameplay testing.
- **Infinite Glider Stamina:** remains disproven for RVA 0x39E73C; the UI correctly disables the old semantic in one capability path, but stale C# patch definitions remain.
- **Health / mana / stamina / god mode / speed / jump hooks:** still not runtime-qualified; latest status keeps the hook framework inactive.

## Source comparison against Drive Current

Drive Current baseline vs user upload:

- 5 added files
- 0 removed files
- 32 changed files

Added:

- `data/qol_resource_profile_1076226.json`
- `src/Architect_QoL_ResourceFeatures.lua`
- `src/Config/Architect_QoL_Config.lua`
- `src/Data/Architect_QoL_Profiles_1076226.lua`
- `tests/code0036/test_qol_integration.py`

Major changed source:

- `runtime/ArchitectRuntime.ps1`
- `runtime/NativeMemoryEngine.cs`
- `runtime/native/ArchitectNativeRuntime.dll`
- `runtime/native/SHA256.txt`
- `runtime/native/source/ArchitectCheatCorrelationEntry.asm`
- `runtime/native/source/ArchitectNativeRuntime.c`
- `runtime/native/source/CheatCorrelationHarness.c/.h`
- `src/mod.lua`
- UI/admin tests

Current uploaded DLL SHA-256: `b057c50808d7ef351efc74793798ecbb9fd595824e7cbfd8edc1f634433302b5`.

The package still reports build identity:

- version `0.40.0`
- buildId `architect-v040-hybrid-admin-code0034-20260918`
- mode `hybrid_observer_and_admin_mutation`

Because functionality/source materially changed after CODE0034, this identity is now ambiguous for provenance even though the DLL hash distinguishes binaries.

## Current-build KFC validation

Authoritative read-only KFC files used:

- `TemplateResource.zip`
- `ItemInfo.zip`
- `BalancingTable.zip`

### Item stacks

`ItemInfo.zip` contains 3,609 records. Exactly 1,901 have `maxStackSize > 1`, with a maximum vanilla stack size of 5000.

This exactly matches the earlier runtime line `stack=1901`, strongly corroborating that the stack-size startup resource pass is operating on the intended current-build field.

### Storage profile

All 12 storage templates in the CODE0036 profile exist in current build 1076226. For all 12:

- exact template name matches
- exact component count matches
- profile `inventorySetupIndex` lands on `keen::ecs::InventorySetup` using Lua 1-based indexing
- original `genericSlotCount` and `availableSlotCount` match the profile

Validation issues: **0**.

This establishes a strong static/resource basis for the corrected storage implementation, but not gameplay persistence/UI semantics.

### Auto Loot profile

Donor `LootTouch_Orb_FogEssence_T1` exists with exactly 14 components. Using EML/Lua 1-based indexing:

- index 4 = `keen::ecs::IsPlayerInRange`
- index 8 = `keen::ecs::PickupItemZone`
- index 11 = `keen::ecs::TriggerShape`

Donor values include `onlyPlayer=true`, an `updateDelay` field, and a Range trigger with `rangeX=1.0`.

Profile validation against current KFC:

- gravity-loot templates: 47 / 47 exist with exact component counts
- material-loot templates: 46 / 46 exist with exact component counts
- gather-drop templates: 462 / 462 exist with exact component counts and exact `ResourceNodePickupDrops` index/type

Validation issues: **0**.

This proves the profile maps to real current-build vanilla data. It does **not** prove that inserting the three donor components into every target has correct runtime semantics.

### Build-zone source

Current `BalancingTable` exposes `buildzoneSizesPerAltarLevel` values 0, 40, 80, 120, 160, 160 on x/y/z. The field targeted by the optional build-zone feature is therefore real. The current QoL config leaves this feature disabled, which is appropriate pending a dedicated test.

## Runtime evidence included in the uploaded package

Latest included native status reports:

- version 0.40.0 / CODE0034 identity
- `loadedInsideGame=true`
- PID 21756
- `buildFingerprintValidated=true`

Latest cheat-correlation state reports:

- `hookFrameworkReady=false`
- `mutationBackendReady=true`
- existing direct-patch readiness flags true
- new `patchFreeCraftReady=true`
- `freeCraft=false`
- `gliderStamina=false`
- `lastFailure=NOT_STARTED`

Executor logs show multiple successful F7 Admin opens and clean process detach/exit. This supports the shell/bootstrap, but not individual cheat semantics.

No `qol_resource_status.json` is packaged with this source snapshot, so storage/Auto Loot runtime semantics after the corrected TemplateResource implementation are not established here.

## Free Craft — meaningful progress

The native runtime adds a hardened `ArchitectPatchRecord`:

- RVA: `0x3822D1`
- expected original: `44 8B A5 08 01 00 00`
- patch: `41 BC 00 00 00 00 90`
- length: 7

The command path now accepts `cheat.freecraft.toggle` and `crafting.free`, with apply/revert through the hardened native patch record.

The latest runtime status has `patchFreeCraftReady=true`, which means the current process passed the native target/readiness check for the expected bytes. This is **runtime target-byte readiness**, not proof that crafting/building costs are actually zero in gameplay.

Recommended next proof: one fresh-process Free Craft ON -> craft/build an item that normally consumes material -> OFF -> repeat and confirm vanilla consumption returns, while preserving status before/after.

## Auto Loot — current source has two owners

The startup resource layer is the Architect-preferred vanilla composition path, but `NativeMemoryEngine.cs` still implements a second Auto Loot behavior by pulsing the E key every ~250 ms via `keybd_event(VK_E, ...)`. `ArchitectRuntime.ps1` toggles that runtime pulse with `SetAutoLoot`.

At the same time, startup config is currently:

- `autoLoot.enabled = true`
- `scope = "full"`
- `pickupRadiusMeters = 16.0`
- gravity = true
- materialPiles = true
- `tuneGatherDrops = true`

That means the current source intends to patch all 47 gravity targets, all 46 material targets, and tune all 462 gather-drop templates before the canary has been user-confirmed.

This conflicts with the comment in the same config saying full scope should only be used after canary proof and conflicts with the desired single-owner architecture.

Recommended correction before runtime test:

- keep only startup ECS/resource Auto Loot
- remove/disarm E-key pulse
- restore `scope="canary"`
- set `tuneGatherDrops=false`
- test one Stone gravity target + one Fog Essence material target
- only then broaden scope in stages

## Teleport — unsafe regression reintroduced

`ArchitectRuntime.ps1` advertises the capability as disarmed in `Get-AdminCapabilities`, and `Dispatch-AdminCommand` still contains a fail-closed ADM-TEST-0002 branch. However `Send-CheatCommand` now special-cases teleport first and calls `Invoke-PlayerTeleport`, bypassing that dispatcher branch.

`Invoke-PlayerTeleport` calls `NativeMemoryEngine.WritePlayerCoordinates`. If the write fails it still returns success (`Teleport queued`).

`NativeMemoryEngine.WritePlayerCoordinates` now contains a real 24-byte `WriteProcessMemory` operation at `target + 0x4` using three integer-converted coordinates.

`EnsurePositionHook` is currently disarmed and no source caller to `SetPlayerTransformAddress` was found, so the path is probably inert while `CapturedPlayerTransform==0`. That does not make the implementation safe: it violates the established fail-closed contract and becomes dangerous if that pointer is ever populated.

The existing ADM-TEST-0002 test explicitly expects `WritePlayerCoordinates()` to return false unconditionally. Current source no longer satisfies that contract.

**Classification: UNSAFE REGRESSION / DO NOT TEST.** Re-disarm before the next build.

## Always Flying — current implementation is not qualified

Current C# registers:

- pattern `F3 0F 10 05 47 53 1D 01`
- patch `F3 0F 10 05 17 66 1D 01`
- fallback RVA `0x22AFE1`

The MIT Shroudtopia historical Flight Mod instead matched `F3 0F 10 05 ?? ?? ?? ?? F2 0F 11 4C ...` and detoured the instruction to a private literal approximately `-1.57000005f`.

The current Architect version is therefore **not simply the proven external mechanism transplanted**. It redirects a RIP-relative load to a different module address whose current value has not been established by the evidence in this package.

Additionally, coding-agent edits removed `IsNativeRuntimeLoaded()` guards from the C# patch engine, and the glider-flight path can fall back to a hardcoded RVA. C# `ApplyPatch` preserves whichever bytes happen to be there, but does not require an expected-original-byte match before a fallback write and does not fail on cache-flush/protection-restoration failure.

**Classification: UNQUALIFIED / DO NOT TEST YET.** Either remap the current-build scalar and implement in the hardened native runtime, or reproduce the external mechanism as an original current-build native implementation with exact expected-byte/signature gates.

## Infinite Glider Stamina

No change in conclusion: the old native RVA `0x39E73C` patch is not infinite stamina. User gameplay proved that it slows glide movement. The current PowerShell capability correctly disables that semantic, but stale C# patch definitions still call a separate pattern `Infinite Glider Stamina`; they should be retired to avoid future accidental use.

## Test/qualification drift

`VERIFICATION_REPORT.txt` claims 289/289 passing, but its timestamp is 2026-09-19 21:04 UTC. Important source changes occurred after it:

- QoL source/test: ~21:16
- QoL config: ~21:31
- native harness/runtime + DLL: ~22:42
- `NativeMemoryEngine.cs`: 2026-09-20 00:53
- `ArchitectRuntime.ps1`: 01:51

Therefore the report does not qualify the uploaded source.

The master `run_all_tests.ps1` does not invoke `tests/code0036/test_qol_integration.py`.

Running the current CODE0036 integration test against the uploaded source fails at `AutoLoot scope configured`; manual inspection also shows the old assumptions for teleport/flight/single mutation ownership no longer hold.

The archive contains nested ZIPs (`Export/Test_Builds/architect_toolkit.zip`, `data/incoming/architect_building_kfc_bundle_1076226.zip`, `tools/ItemObserver.zip`), so the stale report's packaged nested-ZIP pass also cannot describe this final archive as-is.

**Classification: CURRENT PACKAGE NOT OFFLINE-QUALIFIED.**

## Recommended NEXT BUILD

Do not add another feature before one cleanup build closes the current regressions:

1. Re-disarm all teleport UI/direct write paths; `WritePlayerCoordinates` must fail closed until local-player transform ownership is proven.
2. Remove/disarm runtime E-key Auto Loot; preserve the startup vanilla pickup-zone implementation only.
3. Return Auto Loot to canary scope and disable 462-template gather tuning until canary gameplay succeeds.
4. Disarm the C# Always Flying patch until the current-build target/value is independently validated; move the eventual implementation into the hardened native patch/hook layer.
5. Retire stale C# `gliderStamina` semantics.
6. Keep the native Free Craft patch; run an explicit ON/OFF gameplay test next because its target bytes are already runtime-ready.
7. Add CODE0036 tests to `run_all_tests.ps1`, update tests to reflect the accepted architecture, then rerun the entire master suite **after the final source change and packaging**.
8. Bump authoritative Architect build identity for the next candidate so source/binary/runtime evidence cannot be confused with CODE0034.

After that cleanup passes, the next runtime sequence should be:

- Storage expansion gameplay check
- Auto Loot Stone canary
- Auto Loot Fog Essence canary
- Free Craft ON/OFF gameplay semantics

That sequence should produce much more useful progress than adding another dozen UI controls.
