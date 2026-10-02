# Architect F7 Admin Capability Catalog — external artifact intake INC-0010

Status: PLANNED capability research. External artifacts are hypothesis/capability sources only; they do not prove current-build Enshrouded runtime behavior.
Build target: 1076226.

## Sources reviewed
- Ember.zip — configurable Enshrouded mod with resource/data-oriented tweaks.
- enshrouded_1013216.CT — Cheat Engine table explicitly targeting older revision 1013216.
- Enshrouded Building Companion Water Update WIP V2.CT — Cheat Engine building/world tooling reference.
- enshrouded.CT — Cheat Engine table with player/movement/camera/build/world experiments.

## Product direction approved by user
F7 should become Architect's in-game admin/cheat-control console: live toggles, sliders, one-shot commands, inspectors, presets, and diagnostics. F8 remains the build/create/design surface.

## Capability families extracted

### Player / survival
Health, stamina, mana, regen/current/max inspection and later modification; oxygen/breath; body heat/frost; shroud timer; rested bonus; fall damage; durability; stealth/invisibility; parry; spell mana/cast-time tuning.

### Movement / flight
Move speed, crouch/run/sprint/swim speeds, jump force, gravity/fall speed, flight/build-mode flight, vertical movement, slope/walkability, coordinate inspection.

### Travel / map
Save/load/delete waypoints, fixed teleport destinations, fast-travel permissions, world-border bypass candidate, fog-of-war range/removal, location/marker travel controls.

### Inventory / item editor
Selected-item inspection, item ID/hash, stack/amount, replace/change item, reroll gear, item level, enhancements/unlocked upgrades, durability/repair candidate, delete item.

### Crafting / progression / loot
Free crafting, unlock recipes, XP multipliers, skill-point controls, player/item level caps, skill points per level, loot/resource multipliers, gem salvage/slot probabilities, fishing tuning.

### World / game settings
Time of day, day/night duration, plant growth, production time, enemy/boss health/damage/stamina/perception/attack frequency, mining damage, resource/drop amount, ambient/weather/height/shroud fog parameters, map fog.

### Camera / visual / glider
First-person view, camera distance/offsets, glider acceleration/resistance/yaw/pitch/roll tuning, hologram colors/brightness, selected lighting/visual overrides as optional research.

### Building admin / terrain / props
Base/build area size, build range, no-build-zone bypass, build-in-shroud, flame-altar limits, terrain/block override, placed-block flags, prop override/UUID, local/global nudge, rotation, placement flags, break-unbreakable candidate, voxel/material swaps, plant-growth acceleration, terrain/block replacement, terraforming hardness/HP/susceptibility, terrain drop rate.

### Inspector / developer
Last prop looked at, IDs/GUIDs/hashes, coordinates, selected item details, component/runtime diagnostics, current game/build fingerprint, command history.

## Architecture direction
Use a registry-driven AdminAction definition rather than hand-coding each button. Each action should carry: command ID, category, control type, value type/range, evidence status, adapter/backend, authority requirement, persistence scope, live/reload requirement, risk, readback verifier, and revert behavior.

Recommended top-level F7 pages:
1. Dashboard / Quick Toggles
2. Player
3. Movement & Travel
4. Inventory & Items
5. Crafting & Progression
6. World & Game Settings
7. Camera & Glider
8. Building Admin
9. Multiplayer Admin
10. Inspector / Diagnostics

## Implementation policy
Prefer vanilla/resource-backed settings first when current-build evidence supports them; then validated runtime adapters; only then targeted native patches. External CT/Lua implementations are not copied. Every current-build feature must be independently mapped and validated. Save-affecting/world mutation and multiplayer actions remain disabled until authority, lifetime, and readback are proven.

## Acceleration strategy
Research by subsystem batches and use one runtime session to validate multiple read-only candidates. Build the generic AdminAction/adapter framework once so newly proven capabilities become registry entries rather than bespoke UI rewrites.
