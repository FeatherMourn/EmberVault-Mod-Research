# Independent Enshrouded Cheat Engine Table — Phase 1

Artifact: `Enshrouded_Independent_Phase1.CT`

## Evidence captured

- Executable: `H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe`
- SHA-256: `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`
- PE: x64 (PE32+), 8 sections, timestamp field `0x6A4236C8`
- Exact requested reference paths were unavailable.
- Local copies were found under this workspace and inspected for category/behavior vocabulary only.

## Phase 1 status

Infrastructure: Static-analysis complete.

Gameplay features: Not implemented. No feature is claimed functional or ready for live testing.

The table includes numbered groups, module/build diagnostics, an emergency cleanup control, explicit enable/disable blocks, and a documented exactly-one-AOB policy. No gameplay AOB, offset, symbol, or hook was copied from a reference table.

## Feature register

All entries below are currently `Not implemented`; none are `Static-analysis complete`, `Ready for live testing`, or `Live-tested` yet.

- Safe: health, stamina, mana, no fall damage, shroud timer, oxygen/breath, body heat, XP multiplier, durability loss, ammunition consumption, movement speed, jump height, glider parameters, time of day.
- Crafting/progression: free crafting, material-consumption multiplier, stack size, skill points, used skill-point override, upgrade-limit controls.
- Navigation/world: coordinate display, save/load position slots, fixed-location teleportation, map discovery, building reach, building restrictions, structural support, prop placement.
- Experimental: free flight, no-clip, item editing, item deletion, item rerolling, inventory quantity manipulation, terrain destruction, voxel reskinning, automated building.

Each future implementation must add its target-identification record, original-byte/value record, uniqueness result, boundary/return-flow review, preservation review, cleanup proof, risk notes, offline test procedure, and one of the status labels above.

## Required validation before adding hooks

1. Open the table in Cheat Engine and attach only to the matching module.
2. Run the module validation entry and confirm the process name.
3. For each future hook, independently identify the target instruction, verify instruction boundaries and return flow, and record original bytes.
4. Require a scan result count of exactly one before allocation or patching.
5. Verify register, flags, stack, thread, and error-path preservation.
6. Disable the feature and confirm original bytes, allocations, and symbols are restored.
7. Test only offline on a disposable save; multiplayer and save-affecting risks must be documented per feature.

## Important limitation

This Phase 1 artifact is infrastructure only. Assembly or table loading is not evidence that any requested gameplay feature works. Live-tested status requires explicit user gameplay validation.
