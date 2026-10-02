# CODE-0042G1E — Mobility migration source audit

Date: 2026-09-20
Build scope: Enshrouded 1076226
Status: SOURCE-VERIFIED MOBILITY EVENT MIGRATION / SAFETY-METADATA CORRECTION REQUIRED / NO RUNTIME CLAIM

## Source-verified migration result
- `Render-MobilityTravelPage` contains zero direct `Register-SafeUiEvent` registrations.
- `Render-MobilityTravelPage` contains zero direct `.Add_Click(...)` registrations.
- Mobility now has 9 `Register-AdminActionEvent` source-level registrations and 3 `Register-F7UiEvent` registrations.
- Home raw-event count remains zero.
- Player Vitals raw-event count remains zero.
- Registry now contains 54 unique actions.
- `movement.teleport` remains disabled under ADM-TEST-0002.
- Glider stamina remains bound to the semantically-blocked canonical action.
- No prohibited direct F7 calls to TogglePatch, EnableAllSurvival, DisableAllSurvival, WritePlayerCoordinates, ToggleAutoLoot, or ToggleGliderFlight reappeared.

## Critical truthfulness issue in `movement.position.read`
The new registry entry is currently:

- enabled: true
- controlType: `read_only`
- evidenceStatus: `READ_PATH_CANDIDATE`
- backendAdapter: `PositionObserverAdapter`
- backend: `READ_ONLY_OBSERVER`
- runtimeMode: `LIVE`
- risk: `read_only`

This metadata is not supported by the current source architecture.

`PositionObserverAdapter` does not exist in the runtime source, and `READ_ONLY_OBSERVER` is not used by the existing read-only registry entries. Existing read-only inspection actions use established registry vocabulary such as backend `NONE` with adapters like `PlayerAdapter` or `DiagnosticsAdapter`.

More importantly, the current `Get-CurrentPlayerPosition` implementation is not a pure read-only observer path. Its first path calls:

`[NativeMemoryEngine]::ReadPlayerCoordinates([IntPtr]::Zero, ...)`

`ReadPlayerCoordinates` calls `EnsurePositionHook()`. `EnsurePositionHook()` performs native executable-patch work including signature scanning, remote executable allocation, `WriteProcessMemory`, and a detour patch at the target instruction.

Therefore the current position-read control cannot truthfully be represented as a safe enabled read-only observer action. The legacy handler existed before G1E, so G1E did not introduce the native hook behavior, but the new canonical registry identity currently legitimizes it incorrectly.

## Required correction
Fail closed until a genuinely non-mutating qualified position source is proven.

Recommended registry correction for `movement.position.read`:
- enabled: false
- controlType: `read_only`
- evidenceStatus: `UNSOLVED`
- backendAdapter: `None`
- backend: `NONE`
- runtimeMode: `UNAVAILABLE`
- authority: `unresolved`
- risk: `mutation` (because the current implementation path can install an executable detour)
- readbackVerification: `none`
- failureReason: explicitly state that the legacy current-position path depends on `EnsurePositionHook` / executable patching and is disarmed until a safe read-only position source is proven.

Do not remove the EventId or registry identity. Canonical binding should simply make the button disabled/fail-closed.

## Test-fixture drift
The local `test_f7_event_lifecycle.ps1` still expects 53 registry actions. The intentional registry count is now 54, so the fixture needs a narrow update.

The fixture should not merely change `53` to `54`; it should also assert the new action's fail-closed metadata after the safety correction.

## Acceptance status
SOURCE-VERIFIED:
- Mobility raw events 12 -> 0.
- Home and Player remain at 0.
- 54 unique registry actions.
- Event classification migration is structurally complete for Mobility.

NOT YET ACCEPTED:
- `movement.position.read` truthfulness/safety metadata.
- lifecycle test fixture aligned with intentional 54-action registry.

Correct these before migrating the F7 shell.
