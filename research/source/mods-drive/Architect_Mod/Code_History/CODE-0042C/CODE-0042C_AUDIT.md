# CODE-0042C — Binding-audit instrumentation review

Date: 2026-09-20
Game build scope: Enshrouded 1076226
Baseline: Architect Toolkit 0.42.0 / INC-0062
Current ArchitectRuntime.ps1 SHA-256: 3160cdc1efc87914e11c6dc65e1e926e676b8c691b45176e1785cc6c6fb93708
Current admin_action_registry.json SHA-256: c371d7cf02e4bdbbac092a9c4718a0e69fdd49d31f77eadb8db728a5b0a18088
Registry action count: 40
Status: SOURCE-AUDITED / PARTIAL CODE-0042C / NO RUNTIME CLAIM

## Confirmed
- `Get-F7ActionBindingAudit` now exists.
- Startup navigation is normalized to `Show-AdminPage "Home"`.
- `Register-AdminActionEvent` still routes through `Bind-AdminActionControl` and then `Register-SafeUiEvent`.
- The two Developer & Diagnostics controls remain canonically bound to `cheatcorrelation.begin` and `cheatcorrelation.status`.
- Source-consolidation and 224-entry CT catalog presentation remain in place.
- Prohibited direct PowerShell/F7 mutation calls remain absent for `TogglePatch`, `EnableAllSurvival`, `DisableAllSurvival`, `WritePlayerCoordinates`, `ToggleAutoLoot`, and `ToggleGliderFlight`.

## Important limitation in the new audit
`Get-F7ActionBindingAudit` enumerates only `$script:adminActionControls`, which is populated by `Bind-AdminActionControl`. Therefore it reports the controls that are already bound, but it does not provide the denominator of all F7 executable controls.

As written, an audit result with two rows cannot distinguish:
- "all two action controls are bound"
from
- "two of many action controls are bound."

The function is useful for inspecting existing bindings, but it cannot yet prove zero-gap coverage.

## Static legacy-handler evidence
Within the main F7 page-rendering region, static inspection still finds approximately:
- 46 `Register-SafeUiEvent` registrations,
- 50 direct `Add_Click` registrations,
- only 2 `Register-AdminActionEvent` registrations,
- 31 `Send-CheatCommand` call sites,
- 4 `Invoke-PlayerTeleport` call sites.

Not all of those event registrations are gameplay/admin actions; filters, navigation, list selection, view switching, and similar UI-only handlers must remain outside the gameplay action registry. But the current source still contains many action-producing handlers that are not canonically bound.

## Dynamic-action registry gap
The Player Vitals page builds a dynamic `$cheats` array and dispatches `Send-CheatCommand $info.Id`. Eleven of those action IDs are still absent from the 40-entry canonical registry:
- `cheat.godmode.toggle`
- `cheat.mana.toggle`
- `cheat.stamina.toggle`
- `cheat.shroud.toggle`
- `cheat.durability.toggle`
- `cheat.falldamage.toggle`
- `cheat.stealth.toggle`
- `cheat.oxygen.toggle`
- `cheat.cold.toggle`
- `cheat.freecraft.toggle`
- `cheat.autoloot.toggle`

`cheat.parry.toggle` is already present.

These dynamic IDs explain why "all literal Send-CheatCommand IDs resolve" is not sufficient evidence for complete canonical coverage. Dynamic action sources must be audited too.

## Teleport binding gap
The Mobility page contains multiple executable-looking Warp/Safe Spawn controls that call `Invoke-PlayerTeleport`. The function itself correctly fails closed under ADM-TEST-0002, but those controls still need one truthful canonical action identity (for example a single disabled `movement.teleport` capability with parameters) if they remain presented as action controls.

Do not re-enable teleport while adding the identity.

## Acceptance requirement for the next pass
Before responsive migration:
1. create a machine-readable inventory of every F7 event-bearing control, classified as `ACTION` or `UI_ONLY`;
2. every `ACTION` control must have exactly one canonical ActionId;
3. every ActionId must resolve to exactly one registry entry;
4. dynamic action IDs must be covered, not only literal direct calls;
5. disabled/unproven controls stay disabled;
6. no action is enabled merely to make the audit pass;
7. the audit must report total ACTION controls, bound ACTION controls, unbound ACTION controls, UI-only controls, missing registry IDs, and duplicate/ambiguous bindings;
8. zero-gap means `unboundActionControls = 0`, `missingRegistryIds = 0`, and `ambiguousBindings = 0`.

Only after this is green should CODE-0042 proceed to the broad 11-page responsive-layout migration.
