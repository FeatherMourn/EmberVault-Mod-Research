# CODE-0042G1C4 — Lifecycle repair source audit

Date: 2026-09-20
Build scope: Enshrouded 1076226
Current ArchitectRuntime.ps1 SHA-256: 109e3734e1970abc8ad30dd620ea4a6ea0c51c09402786afb5fad27f2a724a2f
Current admin_action_registry.json SHA-256: e4be1f20c0014bcebb671c9b2a2f1e751c259ff4f308637a63a82079262f5e5c
Registry action count: 53
Status: SOURCE-VERIFIED LIFECYCLE FOUNDATION / HEADLESS TEST RESULT USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified
- Legacy `$script:f7EventInventory` is absent.
- Stable event definitions live in `$script:f7EventDefinitions`, keyed by EventId.
- Current live controls live separately in `$script:f7ActiveBindings`.
- `Clear-AdminContent` clears `$script:f7ActiveBindings` and `$script:adminActionControls` before clearing page controls.
- `Bind-AdminActionControl` explicitly accepts `EventId`.
- `Bind-AdminActionControl` no longer references caller-scope `EventName` or `Operation`.
- `Register-AdminActionEvent` registers stable ACTION metadata explicitly before binding.
- Conflicting EventId definitions are compared field-by-field and fail closed.
- `staleOrDisposedActiveBindings` is computed from current active controls.
- `Render-DashboardPage` has zero raw `Register-SafeUiEvent` / `.Add_Click(...)` registrations.
- Registry remains 53 actions.
- Prohibited direct NativeMemoryEngine mutation calls remain absent for TogglePatch, EnableAllSurvival, DisableAllSurvival, WritePlayerCoordinates, ToggleAutoLoot, and ToggleGliderFlight.

## Test-file provenance limitation
The reported new file:
`C:\Users\JoelT\AppData\Local\Temp\architect-code0042-35e945431cb14cfeb86ba1de87e42726\architect_toolkit\tests\test_f7_event_lifecycle.ps1`

is on the user's local temporary workspace and is not currently present in the accessible Drive/Library index. Its exact content and test assertions were therefore not independently audited in this pass.

The reported dedicated lifecycle static-test PASS should be treated as user/Codex-reported until the exact file is synced/attached or otherwise made accessible.

## Next source migration target
`Render-PlayerVitalsPage` currently contains exactly five raw F7 registrations:
1. Enable All Overrides -> `cheat.survival.enable_all`
2. Disable All -> `cheat.survival.disable_all`
3. Fill Health -> `player.health.fill`
4. Fill Stamina -> `player.stamina.fill`
5. Fill Mana -> `player.mana.fill`

The dynamic survival badge loop is already routed through `Register-AdminActionEvent` with stable EventIds and should be preserved.

`Render-MobilityTravelPage` still contains 12 raw registrations and remains deferred until the Player slice is complete.

## Acceptance
The shared source lifecycle foundation is sufficiently repaired to proceed with a narrow Player Vitals event migration.

This does not establish in-game/runtime proof. Responsive layout migration remains deferred.
