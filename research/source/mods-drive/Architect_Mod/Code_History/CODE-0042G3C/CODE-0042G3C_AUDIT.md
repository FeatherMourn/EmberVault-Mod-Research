# CODE-0042G3C — Multiplayer / Quest Tracker audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 21d152fe9976a31b7adc59d6540ee71789a629660df34ae84944f4fb44712e7e
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED G3C EVENT/TRUTHFULNESS MIGRATION / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G3C

`Render-MultiplayerQuestsPage` now uses canonical UI_ONLY events for all four prior raw handler families.

Global:
- `f7.quests.tracker.quarantine.toggle.click`

Filters:
- `f7.quests.filter.all.click`
- `f7.quests.filter.main-flame.click`
- `f7.quests.filter.artisans-survivors.click`
- `f7.quests.filter.exploration-lore.click`

Per valid quest id:
- `f7.quests.item.<questId>.quarantine.toggle.click`
- `f7.quests.item.<questId>.status.toggle.click`

Missing/blank quest ids fail closed:
- buttons disabled
- no handlers
- no generated EventIds
- truthful tooltip/accessibility reason

Quest state remains Architect-local JSON/preferences only.

Truthfulness corrections are present:
- page title: `LOCAL QUEST TRACKER & CO-OP NOTES`
- subtitle explicitly says in-game quest state and multiplayer synchronization are not modified
- scope label says `LOCAL ARCHITECT TRACKER ONLY`
- local tracker quarantine wording replaces multiplayer protection claims
- Home telemetry now says `LOCAL QUEST FLAG: ON/OFF`

Registry remains 55 / 17 / 38.

## Test provenance

Reported by user/Codex:
- Multiplayer/Quests raw `.Add_Click`: 4 -> 0
- all four event families UI_ONLY/local-state
- missing quest-id assertions PASS
- real importer: 55 unique
- PowerShell parse: PASS
- lifecycle fixture: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- schema/adaptor validation: PASS
- G1/G2/G3A/G3B closure preserved
- prohibited mutation scan: clean

No runtime/gameplay proof is established.

## Newly identified command-boundary safety issue before G3D

The Codex currently exposes arbitrary AdminAction registry entries in Player/Developer views.

`Update-CodexDetails` has:
- Player command button -> `Send-CheatCommand <commandId>`
- Developer command button -> direct `Dispatch-AdminCommand`

The current command boundaries do not globally enforce `definition.enabled`.

### `Dispatch-AdminCommand`

It resolves the canonical definition, but before checking `definition.enabled` it has special/prefix routes including:

`^(cheatcorrelation\.|cheat\.)`

which call `Publish-CheatCorrelationCommand`.

Therefore a direct/programmatic call using a disabled registered `cheat.*` action can bypass UI canonical gating.

`Process-ArchitectCommand` admits any registry member and forwards it to `Dispatch-AdminCommand`, so the dispatcher must itself enforce the enabled state.

### `Send-CheatCommand`

It has explicit hard rejections for several known unsafe actions and then an execution-capability gate, but it lacks one generic canonical registry-enabled gate.

Several disabled canonical actions still depend on local capability state rather than the authoritative `enabled=false` registry value.

### Required next step

Before migrating Codex UI events, add one generic canonical-enabled gate at both command boundaries.

This is a safety prerequisite, not a new backend and not a registry-state change.

After the boundary gate is proven, proceed to G3D Codex event migration.
