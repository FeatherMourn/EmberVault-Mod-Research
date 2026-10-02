# Exact reference audit: `enshrouded_1013216.CT`

## Provenance and comparison scope

Reference: `F:\Cheat Engine Tables\Enshrouded\enshrouded_1013216.CT`

Reference SHA-256: `31CCA4A726F7D305F281FC4DF3AF54C550C7A847149BB0B57090DE93C71F6EEA`

Compared executable: `H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe`

Executable SHA-256: `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`

Executable PE image base: `0x140000000`; image size `0x2DA7000`; `.text` raw range begins at `0x400` and has raw size `0x12A5200`. The locations below are current-file match locations converted to image virtual addresses. They are not claims that the table hard-codes those addresses; the table uses AOB scans.

The comparison was static: each signature was wildcard-matched against the installed executable. No table entry was enabled and no gameplay behavior was tested. A one-hit match means only that the byte pattern was found once in this file.

## Exact AOB inventory and current-executable result

`PASS-1` means one match. `FAIL-0` means no match. `WARN-2` means two matches and therefore violates the reference comment that the scan should be unique.

| Feature | Reference scan symbol | Exact signature | Current result |
|---|---|---|---|
| Full health | `network_player_attributes` | `8B 04 91 89 44 24 5C 48 8B 5D` | PASS-1, `0x140233F82` |
| Full stamina | `attribute_save` | `8B 3C 88 33 C9` | PASS-1, `0x14027D8CF` |
| Full mana | `AOBMANA_network_player_attributes` | `C6 44 24 24 00 44 8B` | PASS-1, `0x1402343F5` |
| Easy parry | `client_player_trigger_parry` | `74 78 48 8B 8C 24 88 00 00 00` | PASS-1, `0x140264FF7` |
| Free craft / infinite consume | `aobNeeded` | `30 5B C3 CC CC CC CC CC 48 89 5C 24 18` | PASS-1, `0x1403822A8` |
| Available skill points | `aobCalculateAvalaibleSkillPoints` | `48 89 5C 24 08 48 89 74 24 10 57 48 83 EC 30 41 8B F9 49 8B F0 48 8B D9 41 83 F9 01 73 1D` | PASS-1, `0x14026CB30` |
| Used skill points | `aobCalculateUsedSkillPoints` | `48 89 6C 24 20 41 56 4D 8B` | PASS-1, `0x140C9A4B0` |
| Fall damage | `fall_damage_calculation` | `40 53 48 83 EC 60 41 B8 20 00 00 00 48 8D 54 24 20 48 8B D9 E8 ?? ?? ?? ?? 41 B8 20 00 00 00 48 8D 54 24 20 48 8B CB E8 ?? ?? ?? ?? 84 C0 0F 84 E2 00 00 00` | FAIL-0 |
| Durability | `aobdurability_loss` | `40 55 41 55 48 8D 6C 24 B1 48 81 EC D8 00 00 00 41 B8 50 00 00 00 48 8D 55 E7 4C 8B E9` | PASS-1, `0x1401F6DB0` |
| Shroud | `aobFogResistanceUpdate` | `40 55 41 54 41 55 41 56 48 8D AC 24 18 FF FF FF 48 81 EC E8 01 00 00 41 B8 70 00 00 00 48 8D 54 24 20 4C 8B F1` | PASS-1, `0x14027EA00` |
| Oxygen | `OxygenUpdateHook` | `40 55 41 55 41 56 41 57 48 8D AC 24 38 FF FF FF 48 81 EC C8 01 00 00 41 B8 78 00 00 00 48 8D 54 24 20 4C 8B F9` | PASS-1, `0x1401F8D90` |
| Body heat | `aobbodyheat_depletion` | `40 55 56 48 8D 6C 24 B1 48 81 EC F8 00 00 00 41 B8 60 00 00 00 48 8D 54 24 20 48 8B F1` | PASS-1, `0x14027DFF0` |
| Stealth | `enemy_combat_targets` | `48 89 4C 24 08 55 41 55 48 8D AC 24 58 FD FF FF 48 81 EC A8 03 00 00 4C 8B E9` | PASS-1, `0x140302540` |
| Rested bonus | `rested_buff` | `45 32 E4 44 8B 3C 91 EB 03` | PASS-1, `0x140216A7B` |
| Movement discovery | `aobPlayer_Focus` | `0F 10 00 F2 0F 10 48 10 48 8B 44 24 40` | PASS-1, `0x1402CBB33` |
| Movement speed | `aobVelocity` | `F3 41 0F 59 D9 48 03 C8 48 01 0A F3 48 0F 2C C6 F3 48 0F 2C CC` | PASS-1, `0x14023AE34` |
| Jump | `AobCallInside_Actor_Jump` | `F3 41 0F 11 4F 04 0F 57` | PASS-1, `0x140392A0B` |
| Float stats | `aobReadFloatStats` | `F3 0F 11 34 91 48 8D 4D C0 8B 13` | PASS-1, `0x14035FAFA` |
| Integer stats | `aobReadIntStats` | `44 89 34 91 48 8D 4D E0 8B 13 E8 ?? ?? ?? ?? 40 38 75 E0 0F 85 40 02 00 00` | FAIL-0 |
| XP | `player_level` | `45 01 3C 88 48 8B CB` | PASS-1, `0x14028C4D4` |
| Item capture | `aobCheckSlotEmptyNextCall` | `4C 8B 7C 24 28 48 8B 55` | PASS-1, `0x140388453` |
| Item upgrade capture | `aobLevelWhileUpgrade` | `44 8B 24 91 48 8D 95 B0 72 00 00` | PASS-1, `0x140373ACC` |
| Transform | `is_actor_in_shape_toggle` | `C0 48 2B 01 F3 48 0F 2A C8 48 8B 42 08 48 2B 41 08` | WARN-2, `0x1402C685A`, `0x1403B4E68` |
| Gravity window procedure | `aobWndProc` | `48 89 4C 24 08 55 53 56 57 41 55 41 56 41 57 48 8D AC 24 10 FA FF FF` | PASS-1, `0x140DA6050` |
| Gravity velocity | `aobgravity_apply_velocity_actor` | `F3 0F 58 50 04 F3 0F 58 40 08` | PASS-1, `0x140256C58` |
| Stack size | `stack_size` | `0F B7 40 14 3B C8` | PASS-1, `0x140388378` |
| Slot item count | `slot_items` | `41 89 47 04 48 8B D3` | PASS-1, `0x1403884D0` |
| Day time | `day_time` | `48 89 47 48 49 3B 07` | PASS-1, `0x140CE519A` |
| Glider | `glider` | `F3 41 0F 10 84 24 A4 04 00 00` | PASS-1, `0x14039E73C` |
| Transform data helper | `aobData` | `FF 50 30 8B 44 24 78` | FAIL-0 |
| Gravity helper | `aobgravity_apply_velocity_actor` | `F3 0F 58 42 04 F3 0F 58 5A` | FAIL-0 |

The failures and the two-hit transform scan mean the copied table is not established as compatible with this executable. In particular, it must not be enabled wholesale without a current-build rewrite or runtime confirmation.

## Symbols, allocations, and pointer records

The table registers feature scan symbols and unregisters them on disable. Common allocation sizes are `$1000` for ordinary caves; helper/thread regions use `$100000` or a process-global allocation where shown by the scripts. User data cells include a rested-bonus scalar, jump multiplier, XP multiplier, movement/player-velocity capture, float-stat pointer, integer-stat pointer, item pointer, item-upgrade pointers, position pointer, stack-size cell, slot-count cell, day-time cell, glider cell, and gravity thread state. Exact reference symbol names are listed above where they are part of the scan inventory; a rebuilt implementation should rename them if it is independently rewritten.

Known pointer-record offsets from the reference:

- Captured item amount: pointer plus `0x4`.
- Float stats: twelve displayed fields at offsets `0x0, 0x8, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48, 0x50, 0x58`.
- Integer stats: fifteen displayed fields at offsets `0x0, 0x8, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48, 0x50, 0x58, 0x60, 0x68, 0x70`.
- Item upgrade records: level at pointer plus `0x0`; stats record fields at `0x0` and `0x1` as the reference declares them.
- Stack-size cell is read through pointer plus `0x14`; slot-count cell through pointer plus `0x04`; day-time cell through pointer plus `0x4C`.
- Glider fields are exposed at `0x4A4`, `0x4A8`, `0x4B0`, and `0x4B4`.

These are exact reference records, not independently validated offsets. They require runtime lifetime and type testing before reuse.

## Hook and return-flow structure

The executable hooks follow the standard Auto Assembler pattern: scan, allocate cave, define labels, redirect at the match, execute feature-specific replacement, replay displaced instructions, jump to a return label, and on disable restore the original bytes, unregister symbols, and deallocate. Several short hooks instead register the scan site and use a direct byte replacement. The movement/gravity area additionally has a process-level thread/control state with run, key, and active flags.

The reference scripts contain original-instruction annotations, but the current comparison does not prove their continuation addresses are still valid after a version change. A complete live disassembly must be performed at runtime with the current module loaded and each candidate instruction boundary checked.

## Rebuilt-table provenance

`enshrouded_1013216_rebuilt_reference.ct` is a separate byte-for-byte copy made for isolation. It is a **copied reference implementation**, not an independently rewritten or tested rebuild. The original file remains at its source path and was not modified. The rebuilt copy should be treated as a staging artifact until the failed/non-unique signatures are independently rewritten and runtime-tested.

## What is and is not established

Established: exact XML scan strings, reference symbols, the declared pointer records, the lifecycle operations present in the scripts, and static byte-pattern results against the installed executable.

Not established: gameplay functionality, safe register/flag preservation, stack alignment, object lifetime, persistence, save integrity, server authority, or correctness of any hook after enabling. No feature was enabled during this audit.
