# Enshrouded Master Trainer repair report

## Scope and provenance

The requested `F:\Cheat Engine Tables\...` originals were not accessible. This audit used the following read-only workspace copies:

- Master: `I:\My Drive\Enshrouded Mods\Cheat Tables\Enshrouded_Master_Trainer.CT`
- Reference: `I:\My Drive\Enshrouded Mods\Incoming\2026-09-20\INC-0061\enshrouded_1013216.CT`
- Executable: `H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe`

The requested originals were not overwritten. The output candidate is `Enshrouded_Master_Trainer_Repaired.CT` in the same accessible `Cheat Tables` folder. Because the requested F: destination is unavailable, this is the deliverable location currently possible.

## Audit fingerprints

| Artifact | Size | SHA-256 |
|---|---:|---|
| Master workspace copy | 80,053 | `0a591301a96c5fdf257564dec6d53603eefec4ad7c79a3677bb7b3ecfa707d30` |
| Reference workspace copy | 361,670 | `31cca4a726f7d305f281fc4df3af54c550c7a847149bb0b57090de93c71f6eea` |
| Current executable | 34,302,536 | `AF2F5A1227911D8AA06B3908D6BD021183821CAE14EA91099CB57D0DF990781` |

## Structural comparison

| Property | Master | Reference | Finding |
|---|---:|---:|---|
| Entries | 161 | 224 | Master has additional consolidated/custom content. |
| Auto Assembler scripts | 66 | 164 | Reference has more granular scripts. |
| ENABLE markers | 66 | 164 | Parity within each table. |
| DISABLE markers | 66 | 164 | Marker parity does not prove cleanup. |
| `alloc` calls | 92 | 26 | Master has many allocations requiring dependency review. |
| `dealloc` calls | 71 | 25 | Master has 21 unmatched allocation calls by raw count. |
| `registersymbol` calls | 84 | 49 | Master symbol surface is larger. |
| `unregistersymbol` calls | 84 | 33 | Reference also has symbol cleanup gaps by raw count. |

## Repair map

### Matching / behaviorally equivalent features

The following requested core behaviors are present in both tables and are candidates for comparison, not automatic replacement: health, stamina, mana, easy parry, free crafting, available skill points, used skill points, XP multiplier, no fall damage, durability, shroud timer, oxygen, body heat, movement speed, jump height, player-stat capture, item-pointer capture, glider controls, time of day, inventory stack controls, position save/load, and fixed-location teleportation.

Classification: **Needs review** for every matching feature. The current executable hash was not proven compatible with either table's implementation, and marker parity is not cleanup proof.

### Master-only features

The master contains features not represented as equivalent entries in the audited reference, including broad attribute/stat controls, detailed glider aerodynamics, 3D flight controls, coordinate value records, advanced voxel/building tools, prop transforms, voxel reskinning, water/landscaping brushes, comfort/growth controls, terrain excavation, and a larger teleport destination set.

Classification: **Unsafe to merge** for world-mutating, inventory-mutating, flight, voxel, automation, and terrain features. **Needs review** for read-only or configurable values.

### Reference-only or reference-more-granular features

The reference exposes more granular entries for item rerolling, item deletion, item-level/upgrade inspection, transform/gravity hooks, dynamic teleport slots, and several fixed-location groups. These were not copied into the output.

Classification: **Reference-only** unless an independently reviewed equivalent already exists in the master; item mutation and gravity/flight features are **Unsafe to merge**.

### AOB, symbol, allocation, and cleanup differences

Raw script scans show both tables use implementation-specific allocation and symbol surfaces. The master has empty or minimal disable bodies in several teleport-style scripts and its allocation count exceeds deallocation count. The reference also has cleanup gaps, so it is not a cleanup authority. No AOB signature or offset was copied into the output. Each script that is eventually repaired must be re-derived or independently verified against the current executable and must reject anything other than exactly one match.

### Child value records

The master contains many child records for configurable values (movement, jump, glider, crafting, stack, building, time, and teleport parameters). The reference uses a different granularity and child-record arrangement. Child values are therefore preserved in the output, but no pointer, address, or default was changed automatically.

### Dependency and duplicate-symbol risks

Potential conflicts include shared player-stat/item/position pointers, repeated teleport allocation names such as `mem_tp`, shared `pPlayerPos` dependencies, and global symbols used by multiple child records. These require a per-script dependency graph before any cleanup or merge. A raw name scan is not sufficient to prove safe ownership.

## Feature classifications

| Feature group | Classification |
|---|---|
| Phase 1 core features | Needs review; no automatic code merge performed |
| Phase 2 pointer capture and utility features | Needs review |
| Item quantity editing, deletion, rerolling | Unsafe to merge |
| Upgrade manipulation | Unsafe to merge |
| Gravity/free flight | Unsafe to merge |
| Terrain destruction, voxel editing, world-state modification | Unsafe to merge |
| Building automation | Unsafe to merge |
| Unverified reference-only behavior | Reference-only |
| Any target not independently proven on the current executable | Not implemented |

## What was repaired

The separate output preserves the master organization and feature set and is marked with an independent audit comment. No reference code was blindly substituted. Because the current executable was not proven against the master/reference hooks and the exact F: originals were unavailable, functional script bodies were intentionally left unchanged and risky entries were not merged. This output is therefore a **repair candidate**, not a claim of live functionality.
