# CODE-0042G2C — Combat & AI event migration audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
Current ArchitectRuntime.ps1 SHA-256: 6c4e86642ea160e5c23db96c9c196bb23e55b3f2a822686466af45245af60a23
Current admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED G2C EVENT MIGRATION / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G2C

`Render-CombatAIPage` now contains:

- raw `.Add_Click(...)`: 0
- raw `Register-SafeUiEvent`: 0
- canonical `Register-AdminActionEvent`: 1

Canonical Combat EventId:

- `f7.combat.parry.toggle.click` -> ACTION -> `cheat.parry.toggle`
- Page: `Combat & AI`
- Lifetime: PAGE

`cheat.parry.toggle` remains canonically disabled / `UNSOLVED` / backend `NONE` / runtime `UNAVAILABLE`.

The 11 unsupported Combat/AI placeholder handler sites are gone. Their controls remain disabled/presentation-only without fake ActionIds.

`Send-CheatCommand` now rejects:

- `combat.parry`
- `cheat.parry.toggle`

with `PARRY_UNSOLVED` before native command publication.

Registry remains unchanged at 55 actions / 17 enabled / 38 disabled.

## Test provenance

Reported by user/Codex:

- real registry import: 55 unique
- lifecycle fixture: PASS
- PowerShell parse: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- schema/adaptor validation: PASS
- prohibited mutation scan: clean

The lifecycle fixture remains in the user's temporary reconstructed workspace and is not independently source-audited from Drive in this pass.

## G2D source inventory — World / Camera

`Render-WorldCameraPage` currently has exactly 9 raw source registration sites:

- 3 `Register-SafeUiEvent`
- 6 `.Add_Click(...)`

The three real canonical actions are:

1. time-of-day preset loop -> `world.time_of_day`
   - four runtime buttons: 06:00, 12:00, 18:00, 00:00
2. plant growth -> `cheat.world.plant_growth`
3. pause world time -> `world.time_pause`

The six disabled unsupported placeholder source sites are:

1. Resource Yield multiplier loop
2. Loot Drop multiplier loop
3. Freecam / Flycam
4. Hide HUD
5. FOV loop
6. Timescale loop

Those placeholder handlers only report unsupported status and should be removed rather than given fake action identities.

Current canonical action state:

`world.time_of_day`
- enabled: false
- evidenceStatus: `UNSOLVED`
- backend: `NONE`
- runtimeMode: `LIVE`
- authority: `unknown`
- risk: `mutation`

`world.time_pause`
- enabled: false
- evidenceStatus: `UNSOLVED`
- backend: `NONE`
- runtimeMode: `LIVE`
- authority: `unknown`
- risk: `mutation`

`cheat.world.plant_growth`
- enabled: false
- evidenceStatus: `UNSOLVED`
- backend: `NONE`
- runtimeMode: `UNAVAILABLE`
- authority: `unknown`
- risk: `mutation`

Canonical registry truth must override local capability readiness.

## Dispatch defense-in-depth

Current `Send-CheatCommand` can still route/publish these actions when local capability state is optimistic:

- `world.time_of_day` / `cheat.time.set`
- `world.time_pause`
- `cheat.world.plant_growth`

G2D should add explicit fail-closed rejection branches for these canonical unsupported mutations before native publication.

## Remaining G2 raw source counts

After G2C:

- World / Camera: 9
- Building / Entities: 3

Total remaining G2 raw source sites: 12.

Responsive migration remains deferred.
