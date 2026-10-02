# INC-0061 — External Cheat/Mod Artifact Research Notes

Date: 2026-09-20
Project: Architect Toolkit / Enshrouded Mods
Current project build scope: Enshrouded 0.9.1.2 / revision 1076226 / Hotfix #42
Artifact status: EXTERNAL ARTIFACT OBSERVATION only. Nothing here is current-build runtime proof.

## Research contract
These artifacts are used as hypothesis/evidence seeds only. Do not copy restricted third-party code/assets into Architect. Do not carry addresses, offsets, signatures, layouts, or mutation behavior into current code without independent validation. Prefer vanilla/resource mechanisms when current-build evidence supports them. Unsafe mutations remain fail-closed.

## Files inspected
- enshrouded_1013216.CT — 224 entries; 164 Auto Assembler scripts; 43 typed-data entries; 222 nonempty descriptions. Full child hierarchy parsed, not only script entries.
- enshrouded.CT — 119 entries; 75 script entries.
- enshrouded_server.ct — 78 entries; 42 script entries.
- Enshrouded Building Companion Water Update WIP V2.CT — 73 entries; 27 script entries.
- Ember.zip — Lua/config source tree, 51 files, ~193 KB uncompressed.
- flight_mod.zip — x64 native PE DLL + mod.json.
- Four screenshots supplied with the intake.

## enshrouded_1013216.CT — complete user-facing hierarchy summary
Root Enable 1013216 contains:
- Full Health
- Full Stamina
- Full Mana
- Easy Parry
- Free Craft / Inf. Consume Items
- Set Available Skill Points Min. 999
- Set Used Skill Points To 0
- No Fall Damage
- No Weapon Durability Loss
- No Shroud Decrease
- No Oxygen Decrease
- No Body Heat Timer Decrease In Cold Area
- Stealth Mode (Activate when no enemies present)
- Override Max Rested Bonus To x? -> child x? (iRested, 4 bytes), plus informational child that bonus applies when sheltered + warmth
- [Movement Options] -> Super Movement Speed; Super Jump -> child Force (fJumpMul, float)
- Get Stats (Equip Armor To Populate)
  - float children: Wand Damage; Staff Damage; Two Handed Damage; One Handed Damage; Bow Damage; Dagger Damage; Critical Chance Magic; Critical Chance Melee; Critical Chance Range; Ranged Damage; Melee Damage; Magic Damage
  - integer children: Strength; Constitution (artifact typo: Constiution); Dex; Endurance; Intelligence; Spirit; Stamina; Stamina Reg; Stamina Reg Delay; Mana; Mana Reg; Mana Reg Delay; Health; Health Reg; Health Reg Delay
- XP Multiplier x? -> child x? (fXPMul, float)
- Get Item Pointer (Move Any Item In Inventory)
  - [Pointer] Amount
  - Change Item
  - ReRoll The Item (If Item Is Gear)
  - Get Item Level While Upgrading -> Item Level; Enhancements Amount; Unlocked Upgrades
  - Delete Item
  - Print Hash
- Transform Hook
  - Gravity Handler -> informational hotkey children: R = HotKey Enable; CTRL = Down; Shift = Up
  - [Teleport]
    - [Manual Slots]: Save Position 1 -> Load Position 1; Save Position 2 -> Load Position 2; Save Position 3 -> Load Position 3
    - [Dynamic Slots]: Save Position; Load Position; Delete Position
    - [Fixed Locations]: Gem Forge (1); Ancient Spires/Fast Travels (8); Vaults (6); Misc named destinations (97); Hollow Halls (5) = 117 fixed destination rows total
  - stack size -> child stack size
  - items in slots -> child items in slots
  - day time (temporary) -> child day time
  - glider -> move speed 0.8; lift speed 0.39; descend speed 0.7125; turn speed 70
Two unnamed/duplicate tail entries appear non-product/junk and should not become separate F7 capabilities.

## Selected master-table implementation clues (historical source build only)
- Full Health: AOB `8B 04 91 89 44 24 5C 48 8B 5D`; historical site near enshrouded.exe+206E41. Patch derives a nearby max-like value and writes current health.
- Full Stamina: AOB `8B 3C 88 33 C9`; historical +24B70F; writes 999 to the targeted stamina slot.
- Full Mana: AOB `C6 44 24 24 00 44 8B`; historical +2072B4; writes current from a nearby max-like field.
- Easy Parry: AOB starts `74 78 48 8B 8C 24 88...`; conditional branch is neutralized.
- Free Craft / Inf. Consume Items: AOB starts `30 5B C3 ... 48 89 5C 24 18`; stack-local consumption-related value is forced to zero.
- Available Skill Points: injects `r9d=999` at a historical function entry.
- Used Skill Points: historical function entry changed to return zero.
- No Fall Damage / No Weapon Durability Loss / No Shroud Decrease / No Oxygen Decrease / No Body Heat decrease / Stealth Mode: each artifact implementation short-circuits a target function with an early return. Do not reuse these blindly.
- Rested bonus override: AOB starts `45 32 E4 44 8B 3C 91 EB 03`; writes configured stat value; artifact default is 99.
- Movement-locality hook: AOB starts `0F 10 00 F2 0F 10 48 10...`; captures two player-local velocity-component pointers. Super Movement Speed then gates its multiplier by pointer identity. This is valuable as a local-player correlation hypothesis.
- Super Jump: AOB starts `F3 41 0F 11 4F 04 0F 57`; artifact multiplier defaults to 2.
- Get Stats: two stat-write sites identify stat kinds via hardcoded hash constants and capture value pointers. Use hashes only as external evidence seeds.
- XP Multiplier: AOB `45 01 3C 88 48 8B CB`; historical +2597A8; multiplies the XP delta by fXPMul.
- Item pointer: AOB `4C 8B 7C 24 28 48 8B 55`; historical +340D13; captures an item pointer from stack state.
- Change Item: giant Cheat Engine Lua selector; parsed 3,459 AddItem rows and 2,957 unique pre-dedup names. This should NOT become Architect's hardcoded shipping catalog. Use current ItemInfo/registry discovery instead; preserve hashes only as external research seeds.
- Transform hook: AOB starts `C0 48 2B 01 F3 48 0F 2A C8 48 8B 42 08...`; historical injection near +2A8CD3; captures rdx as a position-like structure. Artifact teleport writes coordinates at +0x4/+0xC/+0x14. This layout requires current-build validation.
- Gravity Handler intercepts keyboard state and a gravity/velocity path. Treat as flight/hover research evidence, not reusable implementation.
- Time of day AOB starts `48 89 47 48 49 3B 07`; artifact uses a day-time scalar with comments 12000=midday and 24000=midnight.
- Glider AOB starts `F3 41 0F 10 84 24 A4 04 00 00`; captures a glider-like structure with child fields around +0x4A4/+0x4A8/+0x4B0/+0x4B4 in this artifact build.

## enshrouded.CT / enshrouded_server.ct — additional capability families
Duplicate capabilities are to be normalized, not exposed as duplicate commands. Additional observed families include:
- alternate health/stamina/mana/oxygen/frost/durability/fog/fall-damage hooks
- movement speed, jump, low gravity, max fall speed, jump variants, build-mode flight
- true first-person, camera distance/stability/offsets
- slope angle controls
- coordinate inspector + movement/gravity/flying speed child fields
- build area size and build part maximum range
- Flame Altar / build-zone / fog / crypt-area controls
- glider flight and stat fields
- block ID capture around artifact offset +0x448
- water rendering/underwater fog/air-swim experiments
- invisibility/status-bar/torch/light/material/texture/resource experiments
Important repeated clue: coordinate/transform hooks share a family around `48 8B 42 08 48 2B 41 08...`.

## Building Companion — additional research clues
Observed building/tool families:
- placed terrain/block override; terrain and block IDs
- block-placement flag override: broken / foliage / terrain-gap behavior
- prop UUID override
- prop placement flags, local/global nudge, quaternion/euler rotation, wall/ceiling/upright/overlap controls
- Break The Unbreakable
- undo-buffer voxel swap by input/output ID and mode
- faster plant growth
- Last Prop You Looked At -> prop UUID/name
- glider flight/stat tuning
- ambient-light disable
- normalized time-of-day override
- world-border bypass
- shroud-timer ignore
- spire-trap disable
- infinite stamina/breath
- map-fog removal
- infinite item use / free crafting / temporary recipe unlock
- Air Swimming, prop swap-on-save, prop scale override (experimental)

Important contradictions / build drift:
- Master table glider fields cluster around +0x4A4/+0x4A8/+0x4B0/+0x4B4.
- Building Companion's current-glider-stat fields cluster around +0x4B4/+0x4B8/+0x4BC/+0x4C0/+0x4C4/+0x4C8/+0x4CC.
Do NOT merge these offsets. This is evidence that builds/structures/semantics differ.

`Last Prop You Looked At` is a useful hypothesis for cursor/target ownership, but Architect Entity Inspector remains UNSOLVED/PARKED until a typed current-build owner is independently mapped.

## Ember.zip — resource-level/API evidence
The source uses an external mod API to enumerate or create game resources and modifies resource data. Observed resource types include:
- keen::VoxelModelResource
- keen::VoxelBlueprintItemRegistryResource
- keen::ItemRegistryResource
- keen::ItemInfo
- keen::BalancingTable
- keen::GameSettingsPresetsResource
- keen::FbUiBundle
- keen::RecipeRegistryResource
- keen::MapMarkerRegistryResource
- keen::ecs::TemplateResource
- keen::SceneResource
- keen::VolumetricFog3Resource
- keen::TerraformingEfficiencyRegistryResource
- keen::BuffType

Observed capability families include stack size, expanded magic storage, max level/cap, skill points per level, cast-time/mana-cost multipliers, buffs, Shroud timer, Flame Altar count/base size, placement/no-build/Shroud rules, fast travel, Fog of War discovery range, glider tuning, terrain/block replacement, terraforming properties, custom blueprint injection, fog, Updraft, gems, loot, crafting, fishing, and intro suppression.

This is strong evidence that some capabilities may have cleaner resource/data-level mechanisms than low-level executable patches. It is NOT proof that Architect currently exposes those APIs or that those fields are stable in build 1076226.

## flight_mod.zip — native disassembly notes
- PE32+ x64 native DLL, not .NET.
- Export: `CreateModInstance` only.
- Imports include VirtualQuery, GetCurrentProcess, VirtualProtectEx, GetSystemInfo, VirtualQueryEx, VirtualAllocEx, GetModuleHandleW.
- User-facing strings: `Flight Mod`, `Enables free glider flight.`, activation/deactivation strings.
- PDB path references a Shroudtopia build tree.
- Pattern bytes embedded at RVA 0x4330 begin `F3 0F 10 05 ?? ?? ?? ?? F2 0F 11 4C`; mask string is `xxxx????xxxx`.
- The scanner starts from the main module and walks committed/executable-readable regions inside an apparent 16 MiB module window.
- On a pattern match, a trampoline/patch payload is constructed. The embedded literal tail includes bytes `C3 F5 C8 BF`, which decode as float approximately -1.57 when interpreted little-endian. Do not assume its gameplay meaning until correlated against the historical/current target instruction stream.
Conclusion: this mod is a native pattern-scan + runtime patch/trampoline implementation. Exact current-build applicability is UNSOLVED.

## Proposed normalized F7 capability model
One F7 action per user-visible capability; external artifacts become evidence sources/backends, never duplicate menu entries.

Player:
- health fill / infinite / inspect
- stamina fill / infinite / inspect
- mana fill / infinite / inspect
- parry assist
- fall-damage override
- durability behavior
- shroud depletion override
- oxygen depletion override
- body-heat depletion override
- rested bonus override
- stats inspector (all master child stats retained individually)

Mobility & Travel:
- movement-speed multiplier
- jump multiplier
- flight/hover/gravity family
- coordinate inspector
- Waypoint Manager: manual/dynamic slots + all 117 fixed table locations represented as data rows, not 117 commands

Items & Progression:
- active item inspector
- amount/stack/slot inspection
- change/replace item
- reroll item
- item level / enhancement count / unlocked upgrade inspection
- delete item
- raw hash/ID in Developer view
- skill points available/used controls
- XP multiplier
- free-crafting/consumption behavior
- recipe unlock only if not already handled by vanilla or a safer supported mechanism

Combat & AI:
- Stealth/aggro control stays semantically separate from vanilla pacify until equivalence is tested

World & Map:
- time inspect/set
- map-fog/discovery controls where uniquely useful
- dangerous border/trap/world bypasses Advanced Admin only

Glider:
- one normalized Glider panel with semantic properties; never expose source-build offsets to normal UI

Build & Terrain Admin:
- building authority/range/zone/altar restrictions
- high-risk break/voxel/prop mutation only in Advanced Admin after current-build validation, readback, and revert/undo safety
- precision prop rotation/nudge/scale belongs primarily to F8 BUILD/CREATE/STUDY rather than duplicate F7 creative controls

Camera & Presentation:
- first-person/freecam/camera-distance/offset/presentation features where vanilla does not already meet the need

Developer:
- raw hashes, resource IDs, build signatures, evidence source, adapter/backend, before/requested/readback/revert, capture tooling

## Vanilla-first dedupe policy
When Enshrouded already exposes a supported setting that achieves the same user intent, F7 should prefer the vanilla mechanism or display it as `Vanilla-managed` rather than ship a redundant memory patch. A separate F7 mutation is justified only if it provides a materially different capability (for example a validated live reversible session override versus a persistent server setting).

Potential exact/near-exact vanilla overlaps to verify at integration time include durability toggle, difficulty/player factors, Shroud time factor, diving time, body-heat factor, glider turbulence, mining/plant/resource/factory factors, XP category factors, enemy/boss factors, pacifyAllEnemies, day/night duration, curse/tombstone settings, and multiplayer role permissions. Similar names are not assumed semantically identical.

## Recommended research order
1. Continue current CODE-0033 observe-only movement/stamina correlation; add artifact signature families as observation probes, not mutations.
2. Resolve local-player ownership/identity around movement + transform before teleport/flight.
3. Validate player attribute/stat identity and read-only readback before any fill/infinite mutation.
4. Validate repeated time-of-day signature family.
5. Resolve glider through current resources/layouts; prefer a validated resource mechanism over old offsets.
6. Build current-registry Item Browser read-only; correlate artifact hashes only as evidence.
7. Building authority: test resource/vanilla mechanisms before executable patches.
8. Entity/prop target mapping only when a typed owner is found; no generic cursor hook promoted from Building Companion.
9. World/save mutation (voxel swap, prop replacement, barriers, quest/progression) last, with test-world-only safety and undo/revert proof.

