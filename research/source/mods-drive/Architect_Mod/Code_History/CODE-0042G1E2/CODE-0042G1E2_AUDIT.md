# CODE-0042G1E2 — Position-read safety correction audit

Date: 2026-09-20
Build scope: Enshrouded 1076226
Status: SOURCE-VERIFIED SAFETY CORRECTION / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified

`movement.position.read` now remains canonically present but fails closed:

- `enabled`: false
- `controlType`: `read_only`
- `evidenceStatus`: `UNSOLVED`
- `backendAdapter`: `None`
- `backend`: `NONE`
- `runtimeMode`: `UNAVAILABLE`
- `authority`: `unresolved`
- `risk`: `mutation`
- `readbackVerification`: `none`

Its description/failure reason explicitly documents the legacy chain:

`Get-CurrentPlayerPosition -> ReadPlayerCoordinates -> EnsurePositionHook`

and the executable detour / process-write risk.

Registry count remains 54 unique actions.

The Mobility control remains bound to:

`f7.mobility.position.read.click -> movement.position.read`

so canonical gating disables it rather than presenting the legacy hook path as a safe observer read.

Home, Player Vitals, and Mobility renderers remain source-clean for direct raw events:

- Home raw direct events: 0
- Player raw direct events: 0
- Mobility raw direct events: 0

No prohibited direct F7 calls to `TogglePatch`, `EnableAllSurvival`, `DisableAllSurvival`, `WritePlayerCoordinates`, `ToggleAutoLoot`, or `ToggleGliderFlight` reappeared.

## Test provenance

Reported by user/Codex:

- PowerShell parse: PASS
- `test_f7_event_lifecycle.ps1`: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- prohibited mutation scan: clean

The lifecycle test file still resides in the user's reconstructed local temp workspace, so its exact contents were not independently source-audited from Drive in this pass.

## Next engineering issue: persistent F7 shell event lifetime

The remaining G1 work is the F7 shell/navigation layer.

Current shell has eight source-level event-registration sites:

1. bounds-save timer `Tick`
2. admin-form `ResizeEnd`
3. admin-form `LocationChanged`
4. admin-form `FormClosing` for bounds save
5. AOB Scanner button click
6. navigation button click loop
7. admin-form `KeyDown` for Escape
8. admin-form `FormClosing` for hide/cancel

Seven are clearly UI/lifecycle-only. The AOB Scanner toggle is an ACTION because it invokes `NativeMemoryEngine.ToggleScanner()`.

Important lifecycle constraint:
`Clear-AdminContent` currently clears all `$script:f7ActiveBindings` and `$script:adminActionControls`.

That behavior is correct for page-owned controls but not for persistent shell controls. If shell events are registered through the existing helpers without a lifetime distinction, navigating pages will erase their active-binding records while the shell controls/handlers remain alive.

Therefore shell migration must first add an explicit PAGE vs SHELL lifetime scope to the event-definition/active-binding architecture, or an equivalent deterministic mechanism.

Do not simply register shell controls into the current PAGE lifecycle.

## Scanner caution

The AOB Scanner must not be classified UI_ONLY.

Current source calls `NativeMemoryEngine.ToggleScanner()` directly.

`EnableScanner()` starts a sweeper that calls `ResolveAll()`, reads captured transform state, and can tick autorun/auto-loot if those states are active.

`DisableScanner()` calls `StopMemorySweeper()`, `UninstallPositionHook()`, and `RevertAll()`.

So scanner canonicalization should be handled as its own ACTION slice after shell lifetime support is proven. Do not invent a read-only registry identity for it.

## Recommended next slice

G1F1:
- add PAGE/SHELL lifetime semantics;
- migrate the seven clearly UI-only shell/lifecycle registration sites;
- leave AOB Scanner as the one intentionally-unmigrated shell ACTION;
- prove shell definitions/bindings persist correctly across page navigation.

Then G1F2 can canonicalize or fail-close the scanner action separately.

Responsive layout migration remains deferred until G1 closure is complete.
