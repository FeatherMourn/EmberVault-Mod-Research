# CODE-0042E — Independent event-inventory audit

Date: 2026-09-20
Game build scope: Enshrouded 1076226
Baseline: Architect Toolkit 0.42.0 / INC-0062
Current ArchitectRuntime.ps1 SHA-256: 39eb41a9db618820ce1bdef4cefd6619ad1de50c85f32a5fa9256c08c8509db5
Current admin_action_registry.json action count: 52
Registry enabled: 17
Registry disabled/planned: 35
Status: SOURCE-AUDITED / PARTIAL CODE-0042E / NO RUNTIME CLAIM

## Confirmed
- `$script:f7EventInventory` exists as an independent collection.
- `Register-F7UiEvent` exists for UI-only classification.
- `Register-AdminActionEvent` records ACTION metadata before routing through `Bind-AdminActionControl` and `Register-SafeUiEvent`.
- `Get-F7ActionBindingAudit` now reports total event controls, ACTION/UI_ONLY counts, bound/unbound ACTION controls, missing registry IDs, duplicate registry IDs, ambiguous bindings, and row detail.
- `movement.teleport` now exists in the canonical registry and is disabled with ADM-TEST-0002 semantics: local-player transform ownership unresolved; coordinate writes remain disarmed.
- Registry IDs are unique.
- The source still contains the safety-cleaned state: prohibited direct F7 mutation calls for TogglePatch, EnableAllSurvival, DisableAllSurvival, WritePlayerCoordinates, ToggleAutoLoot, and ToggleGliderFlight are absent.

## Remaining blocker 1 — the independent inventory is not yet populated by the legacy surface
`Register-F7UiEvent` has definition-only presence: there are currently no UI-only call sites.

`Register-AdminActionEvent` has only three source-level call sites outside its definition: the dynamic Player Vitals badge path and the two Developer & Diagnostics correlation controls.

The broader F7 renderer surface still contains legacy raw event registrations. Static inspection of the renderers currently finds action/UI events registered through raw `Register-SafeUiEvent` and direct `.Add_Click(...)` across Player, Mobility, Items, Combat, World/Camera, Building, Home, Settings, Multiplayer/Quests, Codex, Map/Wayfinder, presets, dialogs, and blueprint views.

Therefore the new audit still cannot truthfully claim full denominator coverage until those raw registrations are migrated or explicitly excluded from the F7 audit scope.

## Remaining blocker 2 — audit has no direct-unclassified metric
The acceptance contract requires `directUnclassifiedEventRegistrations`, but the current `Get-F7ActionBindingAudit` object does not expose it.

Because raw `Register-SafeUiEvent` and `.Add_Click` registrations remain, an audit can currently report zero unbound registered ACTION rows while unclassified action controls still exist outside the inventory.

Required: either eliminate every raw event registration within the defined F7 page-rendering surface, or add a deterministic source/runtime mechanism that identifies them. The preferred end state is no raw event registration in F7 page renderers: every event goes through `Register-AdminActionEvent` or `Register-F7UiEvent`.

## Remaining blocker 3 — inventory lifetime / stale-control accumulation
`$script:f7EventInventory` and `$script:adminActionControls` are initialized once. `Clear-AdminContent` currently only clears WinForms child controls; it does not remove or replace inventory/binding entries for controls that were destroyed during page changes.

Because F7 pages are re-rendered when navigation changes, repeated page visits can accumulate stale Control references and duplicate inventory rows. This can:
- inflate denominator counts;
- retain disposed controls;
- make audit results dependent on navigation history;
- create a memory-retention risk.

Required: make inventory entries lifecycle-safe. Prefer storing stable metadata rather than strong Control references for historical coverage, or use a render-generation/page key and replace/dedupe entries deterministically. Tests should visit all 11 pages and obtain the same final audit regardless of visit order or repeated visits.

## Remaining blocker 4 — ambiguous binding key is not stable
`ambiguousBindings` currently groups ACTION rows by `controlName`. Many dynamically created WinForms controls do not have a unique `.Name`, and multiple controls may have an empty name.

This can create false ambiguity or fail to distinguish distinct controls.

Required: assign each inventoried event a stable `EventId` / `ControlKey` supplied by the renderer or registration helper. Use that stable key for duplicate/ambiguous-binding checks. Do not use display text or `.Name` as the sole identity.

## Known raw registration volume
Across current source there are still many raw registrations. In the principal renderer set, examples include:
- Player Vitals: survival enable/disable; health/stamina/mana fill.
- Mobility & Navigation: speed, jump, autorun, gravity, glider stamina; location filtering; selected/custom/safe-spawn warp; get-position.
- Items & Progression: reroll, duplicate/repair/sort, item search/category, skill-point actions.
- Combat & AI: damage/enemy/crit/parry/attack-speed/knockback/freeze/aggro/kill/despawn/boss controls.
- World & Environment / Camera: time, plant growth, pause, camera/freecam/HUD/FOV/time-scale controls.
- Building & World Editing: altar area/far, build reach.
- Home / Settings: quick vitals, revert-all, subview navigation, panic, save settings/hotkeys.
- Multiplayer / Quests: role/preset/admin controls.
- Codex / Developer: command execution, wiki/open/copy/view actions.
- Map / Wayfinder: filters, waypoint/folder CRUD, presets, dialogs.

Not every raw handler is ACTION. Each must be explicitly classified.

## Required next pass
Finish event classification/binding closure before responsive migration:
1. define the exact F7 audit surface;
2. replace every raw event registration in that surface with `Register-AdminActionEvent` or `Register-F7UiEvent`;
3. add missing truthful registry identities only when a real ACTION control requires one;
4. keep unsupported actions disabled;
5. add stable EventId/ControlKey identity;
6. make inventory lifecycle deterministic across page rerenders;
7. report `directUnclassifiedEventRegistrations` and make it zero;
8. run the existing 53/53 truthfulness and 28/28 UI smoke tests plus new event-inventory tests.

Zero-gap acceptance before responsive migration:
- `unboundActionControls = 0`
- `missingRegistryIds = 0`
- `ambiguousBindings = 0`
- `directUnclassifiedEventRegistrations = 0`
- repeated traversal of all 11 pages produces stable counts and no stale/disposed-control rows.
