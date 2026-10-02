# CODE-0042G1D — Player Vitals event migration audit

Date: 2026-09-20
Build scope: Enshrouded 1076226
Current ArchitectRuntime.ps1 SHA-256: 1ae3fc61f066be664c153d950189ca9aaffbc6d6dd7dd05b76773299188ef628
Registry action count: 53
Status: SOURCE-VERIFIED PLAYER EVENT MIGRATION / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified
- `Render-PlayerVitalsPage` contains zero direct `Register-SafeUiEvent` registrations.
- `Render-PlayerVitalsPage` contains zero direct `.Add_Click(...)` registrations.
- The five requested Player Vitals controls now use `Register-AdminActionEvent` with these EventIds:
  - `f7.player.survival.enableAll.click` -> `cheat.survival.enable_all`
  - `f7.player.survival.disableAll.click` -> `cheat.survival.disable_all`
  - `f7.player.health.fill.click` -> `player.health.fill`
  - `f7.player.stamina.fill.click` -> `player.stamina.fill`
  - `f7.player.mana.fill.click` -> `player.mana.fill`
- The existing dynamic Player survival/cheat badge loop remains on `Register-AdminActionEvent`.
- `Render-DashboardPage` remains clean: zero raw direct event registrations.
- Registry contains 53 unique canonical action IDs. The five Player ActionIds are all present.
- No prohibited direct F7 NativeMemoryEngine mutation calls reappeared for TogglePatch, EnableAllSurvival, DisableAllSurvival, WritePlayerCoordinates, ToggleAutoLoot, or ToggleGliderFlight.

## Test provenance
The reported PowerShell parse, 53/53 truthfulness, 28/28 UI smoke, lifecycle static test, zero UI errors, CT catalog count 224, and prohibited-mutation scan are accepted as user/Codex-reported for this slice.

The exact local `test_f7_event_lifecycle.ps1` remains outside the accessible Drive/Library surface, so its assertions were not independently source-audited here.

## Next migration target: Mobility
`Render-MobilityTravelPage` currently contains exactly 12 raw `Register-SafeUiEvent` source-level registrations and zero direct `.Add_Click(...)` registrations.

Source-level classification:
- ACTION: movement speed loop -> `movement.speed`
- ACTION: jump-height loop -> `movement.jump_height`
- ACTION: MMO autorun -> `movement.autorun`
- ACTION: zero-G/gravity -> `movement.gravity`
- ACTION: glider stamina -> `cheat.world.glider_stamina`
- UI_ONLY: location category filter
- UI_ONLY: location search text
- UI_ONLY: location selection
- ACTION: selected-location warp -> `movement.teleport`
- ACTION: custom-coordinate warp -> `movement.teleport`
- ACTION: current-position read -> needs a truthful canonical read-only identity; no exact registry action currently exists
- ACTION: safe-spawn warp -> `movement.teleport`

`movement.teleport` already exists and remains disabled under ADM-TEST-0002.

The current-position handler calls `Get-CurrentPlayerPosition`, which is read-only and fails with null when no validated source is available. If canonicalized, add only a read-only identity based on the existing registry schema; do not invent a mutation backend or imply runtime proof.

## Acceptance
Player Vitals raw event migration is source-complete.

Mobility is the next bounded slice. Responsive layout migration remains deferred.
