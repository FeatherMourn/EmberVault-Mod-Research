# Enshrouded Master Trainer repaired-table test plan

## Preconditions

- Work offline/local only.
- Back up the save and use a disposable test save.
- Do not test in multiplayer or on a shared server.
- Record the executable SHA-256 before each test session.
- Attach only to `enshrouded.exe`; do not scan all modules.
- Keep the original master, reference, and repaired files separate.

## Per-script static gate

1. Identify the intended behavior and dependency inputs.
2. Verify the target instruction/data structure independently against the current executable.
3. Require exactly one AOB match in the named module.
4. Disassemble enough instructions to verify whole-instruction overwrite boundaries.
5. Record original bytes/values and verify the return path.
6. Check registers, flags, caller/callee-saved state, and x64 stack alignment before calls.
7. Match every allocation with an owned deallocation and every registered symbol with an unregister operation.
8. Check for duplicate symbols and shared-pointer dependencies.
9. Assemble/enable in a suspended disposable test only after the previous gates pass.
10. Disable and verify original bytes, values, symbols, and allocations are restored.

## Phase 1 order

Test one feature at a time: health, stamina, mana, easy parry, free crafting, skill points, used skill points, XP multiplier, no fall damage, durability, shroud timer, oxygen, body heat, movement speed, and jump height.

For each feature, record: `Static validation`, `Ready for live testing`, `Live-tested`, `Failed`, `Unsafe`, or `Needs review`. Assembly success alone is not a passing result.

## Phase 2 order

First validate read-only player-stat and item-pointer capture. Then test glider controls, time of day, stack controls, position save/load, and one fixed teleport destination at a time. Confirm pointer lifetime and nil/invalid-pointer handling before any write.

## Phase 3 risky review

Do not automatically enable item quantity editing, item deletion, item rerolling, upgrade manipulation, gravity/free flight, terrain destruction, voxel editing, building automation, or world-state modification. Each requires separate static review, save-backup verification, and explicit offline user testing.

## Failure handling

If an AOB count is zero or greater than one, stop and mark `Needs review`. If disable leaves any byte, value, symbol, allocation, or pointer state changed, mark `Failed` and do not continue. If behavior is multiplayer-visible or save-affecting, mark the risk and keep the feature disabled by default.
