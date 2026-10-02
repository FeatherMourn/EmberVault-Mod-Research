# CODE-0042D — Dynamic-vitals binding audit

Date: 2026-09-20
Game build scope: Enshrouded 1076226
Baseline: Architect Toolkit 0.42.0 / INC-0062
Status: SOURCE-AUDITED / PARTIAL CODE-0042D / NO RUNTIME CLAIM

## Confirmed
- `admin_action_registry.json` now contains 51 unique canonical actions.
- Enabled actions remain 17; 34 are disabled/planned.
- The 11 newly added dynamic Player Vitals IDs are present and disabled:
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
- The Player Vitals dynamic badge loop now uses `Register-AdminActionEvent -ActionId $c.Id` for qualified/clickable badges.
- Two Developer & Diagnostics bindings remain on `cheatcorrelation.begin` and `cheatcorrelation.status`.
- Startup remains normalized to `Show-AdminPage "Home"`.
- Source-consolidation and the 224-entry CT catalog presentation remain preserved.
- Prohibited direct PowerShell/F7 mutation calls remain absent for `TogglePatch`, `EnableAllSurvival`, `DisableAllSurvival`, `WritePlayerCoordinates`, `ToggleAutoLoot`, and `ToggleGliderFlight`.

## Remaining blocker — denominator is still not independent
`Get-F7ActionBindingAudit` still enumerates `$script:adminActionControls`, which is populated by `Bind-AdminActionControl`. It therefore audits only already-bound controls and still cannot prove how many F7 action controls exist overall.

Current source has three real `Register-AdminActionEvent` call sites at source level: the Player Vitals dynamic loop plus the two Developer & Diagnostics controls. The dynamic loop can bind multiple runtime controls, but broad legacy coverage remains unconverted.

## Known remaining action-producing UI sites
The current F7 renderers still contain action handlers outside `Register-AdminActionEvent`, including:
- Player Vitals: survival enable/disable; health/stamina/mana fill.
- Mobility & Navigation: speed, jump, autorun, gravity, glider stamina, selected-location warp, custom warp, safe-spawn warp.
- Items & Progression: item reroll; skill-points set/presets/reset.
- Combat & AI: Easy Parry.
- World & Environment: time-of-day buttons, plant growth, time pause.
- Building & World Editing: altar area, altar far, build range.
- Home: quick health/stamina/mana and revert-all.
- Mods/Settings: panic/revert-all.
- Codex/Developer command details: dynamic `Send-CheatCommand $cid` and `Dispatch-AdminCommand` execution controls.
- Preset controls indirectly invoke `Invoke-ArchitectPreset`, which can dispatch canonical admin actions and therefore must be classified deliberately rather than ignored.

Teleport controls remain correctly fail-closed, but there is still no canonical `movement.teleport` registry entry. If those controls remain visible as action controls, bind them to one disabled canonical teleport action with ADM-TEST-0002 as the failure reason. Do not re-enable teleport.

## Event-classification requirement
Before broad responsive migration, every F7 event-bearing control should be registered through exactly one of two explicit paths:

1. `ACTION` — gameplay/admin/backend command intent. Must have exactly one canonical ActionId and resolve to one registry entry.
2. `UI_ONLY` — navigation, filtering, list/grid selection, view switching, open/close dialog, clipboard/external-link behavior, or local presentation-only interaction. Must be recorded in the independent event inventory but must not be forced into the gameplay action registry.

For disabled unsupported placeholder controls whose click handler only says “unsupported,” prefer removing the event handler and expressing the reason through disabled state/tooltip/status text. Do not create meaningless registry actions solely to satisfy counting.

Local preset/config/project-data actions should be explicitly classified. If they can indirectly dispatch gameplay actions (for example `Invoke-ArchitectPreset`), treat the user-facing Apply control as ACTION and bind it to a truthful canonical preset action; do not infer success from local UI state.

## Audit architecture needed
Create an independent `$script:f7EventInventory` (or equivalent) populated by both action and UI-only registration helpers. `Get-F7ActionBindingAudit` must derive its denominator from that inventory, not from `$script:adminActionControls`.

It should report at least:
- totalEventControls
- actionControls
- uiOnlyControls
- boundActionControls
- unboundActionControls
- missingRegistryIds
- duplicateRegistryIds
- ambiguousBindings
- directUnclassifiedEventRegistrations

Zero-gap acceptance requires:
- `unboundActionControls = 0`
- `missingRegistryIds = 0`
- `ambiguousBindings = 0`
- `directUnclassifiedEventRegistrations = 0` within the F7 page-rendering surface.

Do not begin broad 11-page responsive migration until this binding closure is green.
