# INC-0060 — External Cheat / Mod Deep Dive for Architect F7

**Target Architect research build:** Enshrouded `1076226`  
**Primary completeness source:** `enshrouded_1013216.CT`  
**Method:** external artifact evidence → technical hypothesis → current KFC correlation → current-build validation plan → original Architect implementation.

## Executive result

This artifact batch is technically valuable enough to **substantially accelerate F7**. The old tables are not current-build authority, but they expose instruction families, attribute hashes, pointer relationships, data layouts, and user-facing capability structure. Several of those semantics can already be tied to build `1076226` game resources without guessing.

The primary table contains **224 recursively parsed entries**, including non-script children, groups, pointer/value children, help rows, and fixed-location entries. The parser did not stop at script-bearing rows. The F7 coverage matrix accounts for every parsed row. The table contains **164 script-bearing entries**, **117 fixed teleport destinations**, and the stats inspector contributes **27 named current-build-matched attributes**.

### Strongest current-build correlations

- **PROVEN current KFC:** all **27/27** stat hashes used by the 1013216 Stats inspector still exist with matching debug semantics on build 1076226.
- **PROVEN current KFC:** the current player `Movement` attribute has the exact old semantic defaults visible in the legacy tables: Walk ~2.3, Run 5, Sprint 8, SwimRun 2, SwimSprint 3.5, DiveRun 2, DiveSprint 3.5.
- **PROVEN current KFC:** `SlopeConfig` is exactly 45° / 55° / 65° / 10° on the current player template, matching the historical slope table. This should be a resource feature, not a native pointer patch.
- **PROVEN current KFC:** `ItemInfo.maxStackSize` supersedes the legacy stack pointer `+0x14`; use the resource field.
- **PROVEN current KFC:** glider tuning has semantic resource fields (`accelerationForward`, air resistances, yaw/pitch/roll). The legacy runtime offsets should not be Architect's primary implementation.
- **STRONG current-static inference:** the historical Full Health code writes current = slot `+8` + slot `+0xC`; current Health layout is `Health, Min, Max_Base, Max_Adder, ...`, which explains the old mechanism as current = Max_Base + Max_Adder.
- **MULTI-ARTIFACT external corroboration:** `flight_mod.dll` and Building Companion independently use the same glider-flight concept: detour a scalar load to a private float of approximately **-1.57000005**. This is a strong current-remap lead, not current proof.
- **PROVEN current KFC:** current `GameSettingsPresetsResource` exposes 37 vanilla difficulty/world settings. We should not build duplicate native cheats for settings vanilla already owns.

## Primary-table completeness and menu preservation

`1013216_F7_Coverage.csv` is the completeness ledger. Every row in the source table is classified as one of:

- a canonical F7 action/toggle;
- a child parameter/readout;
- a menu/group/help row to preserve UX meaning;
- a data entry such as a fixed destination;
- an internal research helper that is explicitly accounted for but should not become a normal F7 user control.

This means the screenshots' children are not lost. Examples include Rested `x?`, Jump `Force`, every Stats child, item level/enhancement/unlock children, the manual/dynamic teleport subcommands, every fixed-location subgroup/destination, stack amount, item amount, time-of-day value, and all glider tuning children.

## Important mechanism findings from the 1013216 table

### Player attributes

**Full Health — external artifact + current KFC corroboration.** Historical AOB `8B 04 91 89 44 24 5C 48 8B 5D`, old injection `+0x206E41`. The hook computes `[rcx+rdx*4] = [slot+8] + [slot+0xC]`. Current Health ordering identifies those semantic slots as `Health_Max_Base` and `Health_Max_Adder`. This gives us a much narrower current-build search hypothesis than generic health scanning.

**Stamina / Mana.** The artifacts expose useful write/read families but do not safely encode current local-player ownership. Current KFC gives exact Stamina and Mana root IDs/layouts, so remapping can now correlate the historical hooks against known attribute families instead of searching blind.

**Survival timers.** Historical Shroud/Oxygen/BodyHeat implementations often `ret` whole update functions. Those are useful function-discovery leads but are too broad to transplant. Prefer a current debit/update point or current attribute pathway with exact readback.

### Stats inspector

The table's float/int hooks compare attribute IDs and capture addresses. All 27 IDs remain valid on build 1076226. This is one of the best near-term F7 features because it can be implemented **read-only first** and gives us a general player-attribute observation primitive for later Health/Stamina/Mana work.

See `1013216_Stats_Current_Build_Mapping.csv` and `Current_Build_Attribute_Map_1076226.csv`.

### Movement

The historical movement parent captures runtime velocity pointers; Super Speed applies a multiplier at a later arithmetic site and Super Jump scales the jump store. Current KFC independently exposes the full Movement attribute family with the old defaults. Architect should first determine whether current Movement attribute storage has a safe live consumer/refresh path; if yes, that is preferable to reproducing brittle historical pointer offsets.

### Items

The table's selected-item family suggests a compact record around an observed pointer: ID/hash near `+0`, amount near `+4`, and roll/metadata near `+8`. The Lua children Change Item / Reroll / Delete all operate on this captured record. Treat this as **save-affecting external evidence**, not a current layout. The useful next experiment is read-only: correlate selected/moved inventory rows with ItemInfo IDs and amount, then infer the lifecycle required for a safe edit.

### Teleport / transform

This table is especially revealing and especially unsafe to copy directly. The transform hook captures `rdx` at old `is_actor_in_shape_toggle +0x2A8CD3`. The observed consumer performs 64-bit integer subtraction and `cvtsi2ss`, so the coordinates are not ordinary floats/doubles.

The Lua teleport routine then repeatedly writes QWORDs at **misaligned** offsets `+4`, `+0xC`, `+0x14` 91 times. Many fixed destinations use huge signed QWORD values, while comments sometimes show human-scale approximate coordinates. This strongly indicates an opaque packed/quantized/floating-origin representation. **Do not reinterpret or directly write these as XYZ floats.** Preserve the raw location library while current transform authority is researched.

`1013216_Fixed_Teleport_Locations.csv` preserves all 117 destination rows. Standard spires/vaults/dungeons should use vanilla fast-travel/map mechanisms when possible; raw coordinate writes stay disabled until current ownership and representation are proven.

### Glider

The primary table exposes four runtime fields; current KFC gives named gliderConfig fields that match the same behavior family. This is a direct example of the desired dedupe policy: one canonical **Glider Tuning** capability, implemented through resources, not four historical pointer edits plus a second Lua mod.

Free glider flight is separate from tuning. Flight Mod + Building Companion both point to the `-1.57f` scalar mechanism, giving us a targeted current-build remap experiment.

## Cross-artifact deduplication rules

The normalized capability map intentionally collapses implementations that do the same job:

- **Stack Size:** one RESOURCE feature (`ItemInfo.maxStackSize`), not CT `+0x14` and Ember separately.
- **Selected Item Amount:** one editor; dedupe 1013216 `[Pointer] Amount` and `items in slots`.
- **Glider Tuning:** one resource-backed panel; no old runtime-offset duplicates.
- **Glider Flight:** one advanced capability; merge Flight Mod and Building Companion evidence.
- **Time of Day:** one absolute clock control; merge 1013216 / client CT / Building Companion.
- **Infinite Stamina:** one canonical capability after current remap; do not expose multiple artifact implementations.
- **Free Craft:** one canonical control; current hardened Architect patch is preferred if runtime semantics pass. Recipe-zeroing remains a narrower fallback/reference.
- **Slope:** current SlopeConfig resource, not memory pointer patch.
- **Build Zone Size:** BalancingTable resource, not the old pointer array.
- **Teleport:** one Travel subsystem with manual saves, dynamic saves, and fixed library; standard destinations delegate to vanilla fast travel where possible.

## Vanilla overlap: remove custom duplicates

Current KFC proves vanilla settings for durability, pacify enemies, player health/mana/stamina factors, body heat/diving/shroud factors, food/starvation timing, mining damage, plant growth, drop amount, production speed, XP by source, enemy/boss factors, day/night duration, weather, fishing difficulty, glider turbulence, and more.

Policy for F7 should be **delegate, not duplicate**:

- `No Weapon Durability Loss` → use vanilla `enableDurability=false`; retire the custom durability patch path.
- `Stealth` → first test vanilla `pacifyAllEnemies`; if it matches intended UX, retire the broad enemy-target function patch. If it does not, keep a separate advanced Stealth capability with distinct semantics.
- Plant Growth Speed → vanilla setting. Keep only an optional **Instant Growth** capability if it is intentionally beyond vanilla and independently validated.
- Source XP multipliers → vanilla. Keep the CT global award multiplier only as an optional All-XP mode because its semantics are broader.
- Day/Night duration → vanilla; absolute Time of Day remains distinct.
- Player health/mana/stamina multipliers are **not** the same as Full/Infinite vitals, so those table capabilities remain valid research targets.

See `Vanilla_GameSettings_1076226.csv`.

## Building Companion research value

Building Companion contributes several F8/F7 developer-grade mechanisms that are not duplicates of the primary table:

- runtime terrain/block material override and block flags;
- prop UUID override, placement flags, local/global nudge, quaternion/Euler rotation, scale;
- last-looked-at prop UUID/name inspector;
- undo-buffer voxel swapping with terrain/block encoding;
- breakability overrides;
- glider flight scalar;
- map fog, barriers, traps, item-use, recipe unlock, and visual experiments.

For Architect, the highest-value building lead is the **Undo Buffer Voxel Swap** because it may map directly to F8 fill/replace/material-conversion workflows. It should begin observe-only on build 1076226.

## Ember Lua research value

Ember demonstrates that many features can be implemented by modifying current resources instead of native memory:

- ItemInfo stack/glider/building data;
- TemplateResource InventorySetup / storage composition;
- BalancingTable build zones, altar limits, progression, shroud, gems/fishing;
- RecipeRegistryResource crafting requirements/knowledge;
- MapMarkerRegistryResource fast-travel eligibility;
- FogOfWarDiscovery range;
- TerraformingEfficiencyRegistryResource material properties;
- SceneResource barriers/no-build behavior;
- SlopeConfig;
- ActorSequence spell/updraft behavior;
- BuffType and fog resources.

Because no license was found in the supplied Ember package, use these as **technical observations**, not code to transplant verbatim. The preferred Architect result is an original implementation using independently confirmed current resource fields.

## Recommended research order

1. **Read-only Player Stats inspector** using the 27 still-valid attribute IDs. This gives us infrastructure that directly accelerates Health/Stamina/Mana.
2. **Resource-backed quick wins:** Stack Size, Glider Tuning, Slope, Storage, Build Zone Size, Flame Altar Limit, vanilla GameSettings delegation.
3. **Free Craft runtime semantic test** on the existing current-build patch candidate.
4. **Current remap of Health / Stamina / Mana / Easy Parry / Fall Damage** using historical AOB families plus known current attribute semantics.
5. **Glider Flight** current-remap using the independently corroborated `-1.57f` scalar lead.
6. **Item inspector before item mutation.** Never start with Change/Reroll/Delete writes.
7. **Teleport read-only transform capture / coordinate decoding** before any write. Preserve the 117-location library now; activate routes later.
8. **Building Companion observe-only work:** last-prop inspector and voxel-swap path before any world mutation.

## Files in this package

- `1013216_F7_Coverage.csv` — every primary table entry/child accounted for.
- `F7_Capability_Normalization.csv` — deduplicated canonical capability proposal across all supplied artifacts.
- `External_Technical_Leads.json` — parsed AOBs, historical RVAs, pointer/value children, Lua usage, Ember resource types, Flight Mod signature/literal.
- `Current_Build_Attribute_Map_1076226.csv` — current player TemplateResource attribute IDs, semantic names, and defaults.
- `1013216_Stats_Current_Build_Mapping.csv` — 27/27 historical stat IDs matched to current build.
- `1013216_Fixed_Teleport_Locations.csv` — all fixed location raw QWORD triplets.
- `Vanilla_GameSettings_1076226.csv` — current vanilla settings for dedupe/delegation.
- `Cross_Table_AOB_Duplicates.txt` — repeated historical signatures across client/server/tables.
- `All_Cheat_Table_Trees.txt` — recursive table trees including non-script children.
- `External_Technical_Leads.json` — machine-readable reverse-engineering leads.

## Evidence boundary

**PROVEN current build** in this report means current KFC/static resource structure or previously accepted current runtime evidence. Historical CE AOBs, RVAs, pointers, and another mod's behavior remain **EXTERNAL ARTIFACT** until remapped and independently validated on 1076226. Compilation or a matching pattern alone is not gameplay proof.
