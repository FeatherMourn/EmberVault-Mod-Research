# CODE-0023 — GameSettings current-build static research

## Scope and decision

This is an offline-only review of the installed Enshrouded build `1076226`,
its local reflection cache, the audited Architect KFC subset, manifests, and
existing static reports. It did not launch or attach to the game, inspect live
memory, install hooks, or copy offsets/AOB code from an external artifact.

The installed executable is SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
The reflection source is the installed read-only
`H:\SteamLibrary\steamapps\common\Enshrouded\.cache\types.json`.

**Decision:** build 1076226 statically proves a vanilla, aggregate game-settings
model and a purpose-named admin action/event path. It does **not** yet prove a
safe Architect mutation or readback adapter. All mutations therefore remain
disabled. The aggregate settings are high-value candidates for a future
`LIVE` adapter; their current supported runtime mode is `UNAVAILABLE`.

## Authoritative model evidence

Reflection defines `keen::ecs::GameSettings` (type index `2702`, size `0x90`)
and an equivalent `keen::ds::ecs::GameSettings` (index `9876`). The complete
layout is:

| Offset | Field | Reflected type |
|---:|---|---|
| `0x00` | `playerHealthFactor` | `float` |
| `0x04` | `playerManaFactor` | `float` |
| `0x08` | `playerStaminaFactor` | `float` |
| `0x0C` | `playerBodyHeatFactor` | `float` |
| `0x10` | `playerDivingTimeFactor` | `float` |
| `0x14` | `enableDurability` | `bool` |
| `0x15` | `enableStarvingDebuff` | `bool` |
| `0x18` | `foodBuffDurationFactor` | `float` |
| `0x20` | `fromHungerToStarving` | `Time` |
| `0x28` | `shroudTimeFactor` | `float` |
| `0x2C` | `tombstoneMode` | `TombstoneMode` |
| `0x2D` | `enableGliderTurbulences` | `bool` |
| `0x2E` | `weatherFrequency` | `WeatherFrequency` |
| `0x2F` | `fishingDifficulty` | `GenericDifficulty` |
| `0x30` | `miningDamageFactor` | `float` |
| `0x34` | `plantGrowthSpeedFactor` | `float` |
| `0x38` | `resourceDropStackAmountFactor` | `float` |
| `0x3C` | `factoryProductionSpeedFactor` | `float` |
| `0x40` | `perkUpgradeRecyclingFactor` | `float` |
| `0x44` | `perkCostFactor` | `float` |
| `0x48` | `experienceCombatFactor` | `float` |
| `0x4C` | `experienceMiningFactor` | `float` |
| `0x50` | `experienceExplorationQuestsFactor` | `float` |
| `0x54` | `randomSpawnerAmount` | `RandomSpawnerAmount` |
| `0x55` | `aggroPoolAmount` | `AggroPoolAmount` |
| `0x58` | `enemyDamageFactor` | `float` |
| `0x5C` | `enemyHealthFactor` | `float` |
| `0x60` | `enemyStaminaFactor` | `float` |
| `0x64` | `enemyPerceptionRangeFactor` | `float` |
| `0x68` | `bossDamageFactor` | `float` |
| `0x6C` | `bossHealthFactor` | `float` |
| `0x70` | `threatBonus` | `float` |
| `0x74` | `pacifyAllEnemies` | `bool` |
| `0x75` | `tamingStartleRepercussion` | `TamingStartleRepercussion` |
| `0x78` | `dayTimeDuration` | `Time` |
| `0x80` | `nightTimeDuration` | `Time` |
| `0x88` | `curseModifier` | `CurseModifier` |

Supporting reflected types establish a coherent vanilla mechanism:

| Type | Layout | What it proves | What it does not prove |
|---|---|---|---|
| `AdminChangeGameSettingsAction` index `2703` | size `0x98`; settings `+0x00`; `VersionedData` `+0x90` | A purpose-named versioned action can carry the complete aggregate | Callable dispatch boundary, caller authorization, or acceptance |
| `GameSettingsChangedEvent` index `3410` | size `0x98`; new settings `+0x08` | A purpose-named event can publish a complete changed value | Event producer, subscriber timing, or authoritative ownership |
| `ServerConsumedPlayerInput` index `2784` | server-only/dynamic/do-not-save; consumed action version at `+0xC4` | Server-side input accounting explicitly includes this action | The action payload queue, permission rule, host/client route, or result |
| `GameSettingsPresetConfig` index `4309` | preset ID `+0x00`; settings `+0x08` | Presets contain full aggregate values | Current preset values in the installed data |
| `GameSettingsPresetsResource` index `4311` | size `0x128`; min `+0x00`, max `+0x90`, presets `+0x120` | Vanilla resource owns bounds and preset aggregates | Loaded resource identity, current pointer, defaults, or refresh semantics |

The duplicated `keen::ds` resource uses a larger host-side container layout
(`0x148`) but preserves the two `GameSettings` values and presets relationship.
The existing `client_player_input_static_map.json` independently records the
reflected `consumedAdminChangeGameSettingsAction` field, but its mapped native
consumer is not semantic proof of the settings action's dispatch.

## Capability assessment

`PROVEN_STATIC_BUILD_1076226` below means the setting is an explicit field in
the aggregate. It does not mean Architect can change it. `CANDIDATE_LIVE`
means the action plus changed-event design makes live application plausible;
it is a research priority, not a supported runtime classification.

| Requested capability | Current-build source evidence | Candidate mode | Evidence status | Readback / revert feasibility | Contradictions or missing proof |
|---|---|---|---|---|---|
| Player health / mana / stamina multipliers | Aggregate fields `+0x00/+0x04/+0x08` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Full aggregate event could provide readback and captured original could provide revert, but neither route is mapped | Player vital components are server-only; no consumer/cache or owner behavior proven |
| Body heat | `playerBodyHeatFactor +0x0C` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same aggregate readback/revert hypothesis | Consumer and refresh behavior unknown |
| Breath / diving time | `playerDivingTimeFactor +0x10` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Field names diving time, not a direct breath timer; consumer unknown |
| Shroud time | `shroudTimeFactor +0x28` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Does not prove effect on already-running Shroud timers |
| Food / starvation timing | duration factor `+0x18`, starving delay `+0x20`, debuff toggle `+0x15` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Existing buffs/timers may cache values; no reset/refresh mapped |
| Mining damage | `miningDamageFactor +0x30` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Consumer unknown |
| Plant growth | `plantGrowthSpeedFactor +0x34` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Existing growth jobs may cache deadlines |
| Resource/drop amount; loot multiplier | `resourceDropStackAmountFactor +0x38` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Reflection proves resource stack factor, not every loot table or container |
| Production time | `factoryProductionSpeedFactor +0x3C` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Existing jobs may cache completion time |
| Durability enable/disable | `enableDurability +0x14` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Existing durability state and repair behavior not established |
| Combat / mining / quest XP | aggregate factors `+0x48/+0x4C/+0x50` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Exploration and quests share one field; no award-site test |
| Enemy damage / health / stamina | aggregate factors `+0x58/+0x5C/+0x60` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Spawn-time versus dynamic application is unknown |
| Enemy perception | `enemyPerceptionRangeFactor +0x64` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Existing AI perception caches unknown |
| Enemy attack frequency / simultaneous attackers | `aggroPoolAmount +0x55`, `threatBonus +0x70`; UI localization explicitly names both concepts | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_CANDIDATE_BUILD_1076226` | Aggregate readback possible only after mapping | No reflected field literally named attack frequency; mapping from UI concept to these fields is not proven |
| Boss damage / health | `bossDamageFactor +0x68`, `bossHealthFactor +0x6C` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Existing boss instances may be initialized from settings |
| Day / night length | `dayTimeDuration +0x78`, `nightTimeDuration +0x80` | `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_BUILD_1076226` | Same | Active clock phase adjustment behavior unknown |
| Time of day | No distinct time-of-day value/action found in the reviewed aggregate or focused reflection search | `UNAVAILABLE` | `UNSOLVED` | None | Day/night duration is not clock position |
| Crafting recipe requirements | `RecipeRegistryResource`, `RecipeInputResource`, and item/category/count records exist; audited KFC subset includes a recipe registry export | `RELOAD_CANDIDATE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_RESOURCE_SHAPE`; mutation `UNSOLVED` | Offline file diff could verify an authored resource, but no supported load/override mechanism exists | Existing index documentation says recipe-input coverage is not generally complete; no safe refresh |
| Recipe unlocking | Knowledge-related reflected records exist, but no central GameSettings field or validated action was identified | `UNAVAILABLE` | `UNSOLVED` | None | Resource presence does not prove per-player unlock authority |
| Player / item level caps | No corresponding GameSettings field or focused reflected cap resource identified | `UNAVAILABLE` | `UNSOLVED` | None | External catalog hypothesis has no current-build mechanism |
| Skill points per level | `SkillTreeResource` exists; no points-per-level setting identified | `UNAVAILABLE` | `UNSOLVED` | None | Skill tree topology is not progression award policy |
| Spell cast-time / mana-cost settings | No aggregate field or focused reflected resource with those global semantics identified | `UNAVAILABLE` | `UNSOLVED` | None | Per-spell resources may exist, but no authoritative current source/override was established |
| Fog visual parameters | `VolumetricFog3Resource` index `6144`, size `0xD4`, exposes materials, extinction, height, camera fade, barrier thickness/noise | `RELOAD_CANDIDATE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_RESOURCE_SHAPE` | Resource serialization might permit offline verification; live loaded-object readback is unmapped | Visual fog is not Shroud gameplay time or fog-of-war state; no safe resource override/refresh |
| Shroud visual parameters | Fog resource exposes dangerous/deadly barrier visual materials and thickness | `RELOAD_CANDIDATE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_RESOURCE_SHAPE` | As above | Visual parameters must not be represented as gameplay Shroud authority |
| Fast travel / fog of war | No centralized setting or validated admin action identified in focused reflection search | `UNAVAILABLE` | `UNSOLVED` | None | Fog rendering resources do not establish fog-of-war or travel authority |
| Glider tuning | `GliderConfig` index `3793`, size `0x20`: acceleration, three resistance axes, yaw/pitch/roll speed, updraft charge threshold; aggregate has turbulence toggle | Config: `RELOAD_CANDIDATE`; turbulence: `CANDIDATE_LIVE`; supported: `UNAVAILABLE` | `PROVEN_STATIC_RESOURCE_SHAPE`; toggle `PROVEN_STATIC_BUILD_1076226` | Config source identity and loaded-object readback unmapped; aggregate hypothesis as above | A reflected config shape is not a located resource instance or override path |
| Base / building-area settings | No corresponding field in `GameSettings`; building resource subset covers materials, voxel blueprints, recipes, and terraforming efficiency | `UNAVAILABLE` | `UNSOLVED` | None | Building catalog coverage must not be generalized into area-limit authority |
| Building restriction settings | No corresponding field/action/resource identified in the reviewed evidence | `UNAVAILABLE` | `UNSOLVED` | None | Placement observers are downstream and do not prove restriction policy authority |

## Runtime-mode and safety conclusions

No setting is presently supported as `LIVE`, `SESSION`, or `RELOAD` by
Architect. The likely research split is:

- **Aggregate action candidates (`CANDIDATE_LIVE`)**: every explicit
  `GameSettings` field. Promote only after locating the vanilla action producer
  and dispatcher, proving host/server authorization, observing a matching
  `GameSettingsChangedEvent`, and showing at least one real consumer changes
  without restart.
- **Resource candidates (`RELOAD_CANDIDATE`)**: recipes, glider config, and fog
  visuals. Promote only after a resource identity, supported override/load
  route, serialization fidelity, and refresh semantics are independently
  established. Until then they are `UNAVAILABLE`, not `RELOAD`.
- **Unsolved**: time-of-day position, recipe unlock authority, caps, skill
  points per level, global spell tuning, fast travel/fog-of-war, building area,
  and building restrictions.

The preset resource is especially useful for future range/default metadata,
but the audited building-focused KFC bundle does not contain
`GameSettingsPresetsResource`. Architect's existing data-index documentation
also states that the raw installed `.kfc` and `.kfc_resources` archives have no
project-verified decoder preserving resource identity. Therefore no default,
minimum, maximum, or preset numeric values are claimed here.

## Required readback/revert contract for a future adapter

A future mutation must send the entire versioned aggregate through the proven
vanilla route rather than patching an isolated address. Before the first write,
it must obtain and retain the authoritative aggregate. Completion requires an
independently observed changed event (or a separately mapped authoritative
query) whose full aggregate equals the requested result. Revert must submit the
captured original through the same route and verify it identically. Timeout,
authority rejection, absent event/query, partial equality, build mismatch, or
world/session transition must fail closed and must not report `completed`.

## Recommended single-session validation batch

Once a read-only event/query observer and the legitimate admin-action dispatch
are mapped, use a private host world and change several orthogonal settings in
one aggregate: day duration, durability toggle, mining XP factor, production
speed, and glider turbulence. Capture the original aggregate, submit one
versioned change, require exact event/query readback, then behaviorally test a
day-clock interval, one durability use, one mining XP award, one fresh
production job, and one glider flight. Re-submit the captured original and
require exact readback again before shutdown. Do not run this batch until the
authority and readback prerequisites are proven.

## Sources reviewed

- Installed build-1076226 `.cache/types.json` reflection metadata.
- `bridge/client_player_input_static_map.json` (offline static/reflection map).
- `docs/tools/ArchitectDataIndex.md` and the audited
  `data/kfc_sources/building_1076226` family set.
- `bridge/architect_engineering_state.json` and current research documents for
  evidence terminology and known authority limitations.
- Installed executable identity only; no external trainer, CE table, AOB, or
  proprietary implementation was used.
