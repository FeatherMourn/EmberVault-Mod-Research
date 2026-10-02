# CODE-0042G2D — World / Camera event migration audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
Status: SOURCE-VERIFIED G2D EVENT MIGRATION / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G2D

The current Drive source shows `Render-WorldCameraPage` migrated to canonical action bindings:

- time-of-day preset loop -> `world.time_of_day`
- plant growth -> `cheat.world.plant_growth`
- pause world time -> `world.time_pause`

Stable runtime EventIds:

- `f7.world.time.set.6.click`
- `f7.world.time.set.12.click`
- `f7.world.time.set.18.click`
- `f7.world.time.set.0.click`
- `f7.world.plantGrowth.toggle.click`
- `f7.world.time.pause.click`

The time preset loop constructs EventIds with invariant integer formatting.

The pause handler now computes the requested state first, dispatches, and changes `$script:timePaused`, button text, and color only after a successful result. A rejected dispatch leaves local UI/session state unchanged.

`Send-CheatCommand` explicitly rejects before native publication:

- `world.time_of_day` / `cheat.time.set`
- `world.time_pause`
- `cheat.world.plant_growth`

The six unsupported placeholder handler families were removed:
- Resource Yield
- Loot Drop
- Freecam/Flycam
- Hide HUD
- FOV
- Timescale

Registry remains 55 actions / 17 enabled / 38 disabled.

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

## G2E source inventory — Building / Entities

`Render-BuildingEntitiesPage` has exactly 3 remaining raw `Register-SafeUiEvent` source registrations:

1. No Flame Altar Build Limit
   - `cheat.world.altar_area`

2. Place Flame Altar Anywhere
   - `cheat.world.altar_far`

3. Extended Build Reach
   - `cheat.world.build_range`

All three already have canonical registry entries and all remain disabled / `UNSOLVED` / backend `NONE` / runtime `UNAVAILABLE` / unknown authority / mutation risk.

The rest of the Building/Entities renderer is already presentation-only for unsupported operations:
- Instant Dismantle
- Flatten
- Excavate
- Rotate
- Clone
- Entity Teleport
- Kill Entity
- Despawn Entity

Those controls have no handlers and should remain that way.

Current `Send-CheatCommand` still maps altar area/far aliases toward native publication and can publish build range by default when local capability state is optimistic. G2E should therefore add explicit fail-closed rejection before publication for all three building actions.

## G2 closure target

After G2E:

- Building/Entities raw events = 0
- World/Camera raw = 0
- Combat/AI raw = 0
- Crafting/Progression raw = 0
- Inventory raw = 0
- G1 Home/Player/Mobility/shell raw = 0

That will source-close the bounded G2 event migration. Responsive page-layout migration remains deferred.
