# CODE-0042G1F2 — G1 source/offline closure audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
Status: SOURCE-VERIFIED G1 EVENT CLOSURE / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G1F2

Current registry:
- 55 unique actions
- 17 enabled
- 38 disabled

New canonical scanner action:
- `diagnostics.aob_scanner.toggle`
- enabled: false
- evidenceStatus: `UNSOLVED`
- backendAdapter: `DiagnosticsAdapter`
- backend: `NONE`
- runtimeMode: `UNAVAILABLE`
- authority: `unknown`
- risk: `mutation`

Current shell binding:
- EventId: `f7.shell.scanner.toggle.click`
- ActionId: `diagnostics.aob_scanner.toggle`
- Classification: ACTION
- LifetimeScope: SHELL

Current PowerShell contains:
- zero direct calls to `NativeMemoryEngine.ToggleScanner()`
- zero direct calls to `NativeMemoryEngine.EnableScanner()`
- zero direct calls to `NativeMemoryEngine.DisableScanner()`

`Send-CheatCommand` has an explicit fail-closed scanner route before the native command-publication path.

The scanner control is presented as unavailable and canonical action gating keeps it disabled. The badge updater does not re-enable the control or mutate native scanner state.

`Get-CurrentPlayerPosition` remains fail-closed and returns `$null`; Home continues to report coordinates as unavailable rather than reaching the native position hook.

## G1 raw-event closure

Source state:
- Home raw direct events: 0
- Player Vitals raw direct events: 0
- Mobility raw direct events: 0
- shell UI-only raw events: 0
- shell raw ACTION events: 0

Therefore the bounded G1 source-event migration is source-closed.

This does not establish in-game/runtime behavior.

## Test provenance

Reported by user/Codex:
- real registry import: 55 unique
- schema violations: 0
- adapter mismatches: 0
- lifecycle test: PASS
- PowerShell parse: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- prohibited mutation scan: clean

The temporary lifecycle test remains in the user's reconstructed local workspace and is not independently source-audited from Drive in this pass.

## G2 source inventory

Current raw direct event registrations in the planned G2 page set:

- `Render-InventoryItemsPage`: 7
- `Render-CraftingProgressionPage`: 3
- `Render-ProgressionGearPage`: 0
- `Render-CombatAIPage`: 12
- `Render-WorldCameraPage`: 9
- `Render-WorldBuildingPage`: 0
- `Render-BuildingEntitiesPage`: 3

Total G2 raw-event sites: 34.

Recommended bounded sequence:
- G2A — Inventory & Items: 7
- G2B — Crafting / Progression: 3
- G2C — Combat & AI: 12
- G2D — World / Camera: 9
- G2E — Building / Entities: 3

Responsive layout migration remains deferred until event migration closure.
