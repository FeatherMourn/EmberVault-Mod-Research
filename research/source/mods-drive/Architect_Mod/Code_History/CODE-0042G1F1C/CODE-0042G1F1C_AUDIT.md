# CODE-0042G1F1C — Fail-closed position helper audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
Current ArchitectRuntime.ps1 SHA-256: f6478ee95d630414c99ef2505ad63906aadaaa14512b1e3a7eb772624f2a4d98
Current admin_action_registry.json SHA-256: 26cbca50914043a6ce038d0148e91319d23fdd3592b82923672009f8b68523cf
Current NativeMemoryEngine.cs SHA-256: e76a613d5c8d7566015f597c785157fa69cd9493fb0fce331740d3a0216ef82e
Registry actions: 54
Enabled: 17
Disabled: 37
Status: SOURCE-VERIFIED POSITION-HELPER SAFETY CLOSURE / SCANNER ACTION STILL RAW / NO RUNTIME CLAIM

## Source-verified

`Get-CurrentPlayerPosition` is now fail-closed and non-mutating.

Current implementation:

```powershell
function Get-CurrentPlayerPosition {
    # Build 1076226 local-player position ownership is UNSOLVED. Native
    # hook-backed reads are intentionally disarmed; callers must tolerate $null.
    return $null
}
```

Source-level checks:
- PowerShell references to `NativeMemoryEngine.ReadPlayerCoordinates`: 0
- PowerShell references to `NativeMemoryEngine.ToggleScanner`: 1
- the only remaining `ToggleScanner` reference is the raw F7 AOB Scanner button
- Home telemetry displays `Coordinates: UNAVAILABLE (safe source unresolved)` when no safe source exists
- the old `AOB Scanner Verified` claim is absent
- `movement.position.read` remains disabled / `UNSOLVED` / backend `NONE` / runtime `UNAVAILABLE` / mutation-risk
- registry remains 54 actions, 17 enabled / 37 disabled

## G1 state

The bounded G1 page/shell event migration is now source-clean except for one intentionally raw shell ACTION:

`Register-SafeUiEvent $script:btnScannerToggle "Click" ...`

That handler still directly calls:

`[NativeMemoryEngine]::ToggleScanner()`

Home, Player Vitals, and Mobility direct raw event counts remain zero.

Shell UI-only raw events remain zero.

## Scanner source behavior

The native scanner is not a harmless presentation toggle.

Current C# behavior:

- `ToggleScanner()` calls `EnableScanner()` or `DisableScanner()`.
- `EnableScanner()` starts the memory sweeper when a process handle exists.
- `StartMemorySweeper()` repeatedly calls `ResolveAll()`, reads captured player transform state, and may tick autorun / auto-loot when those states are active.
- `DisableScanner()` calls `StopMemorySweeper()`, `UninstallPositionHook()`, and `RevertAll()`.
- `UninstallPositionHook()` can revert executable bytes and free remote memory.
- `RevertAll()` reverts every active registered patch and clears bridge soft toggles.

Therefore F7 should not expose this legacy scanner as an enabled general-purpose diagnostic toggle.

## Recommended G1F2 closure

Canonicalize the scanner as a disabled, fail-closed ACTION:

- commandId: `diagnostics.aob_scanner.toggle`
- EventId: `f7.shell.scanner.toggle.click`
- classification: ACTION
- lifetime: SHELL
- adapter: `DiagnosticsAdapter`
- backend: `NONE`
- evidence: `UNSOLVED`
- runtime: `UNAVAILABLE`
- authority: `unknown`
- risk: `mutation`
- enabled: false

Remove the direct PowerShell call to `NativeMemoryEngine.ToggleScanner()`.

Use a fail-closed canonical handler. If routed through `Send-CheatCommand`, add an explicit rejection branch so programmatic invocation cannot fall through to native command publication.

The scanner button should present as unavailable/disabled rather than standby/live.

Native C# scanner infrastructure should remain untouched in this slice.

## G1F2 acceptance

- registry: 54 -> 55 actions
- enabled: remains 17
- disabled: 37 -> 38
- real registry import succeeds
- shell UI-only raw events = 0
- shell raw ACTION events = 0
- Home / Player / Mobility raw events = 0
- PowerShell direct calls to `NativeMemoryEngine.ToggleScanner` = 0
- canonical scanner EventId exists with SHELL lifetime
- scanner action is disabled and fail-closed
- lifecycle fixture passes with 55-action expectation
- existing truthfulness/UI-smoke/catalog/safety gates remain green
- no runtime/gameplay proof is claimed

After this, G1 can be considered offline/source-closed and the next migration batch can move to G2.
