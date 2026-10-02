# Independent implementation-pattern catalog

This document abstracts the supplied table into reusable design patterns without reproducing its identifiers, signatures, offsets, comments, or assembler blocks.

## Pattern A — module-relative AOB hook

Purpose: locate a current-build instruction site without relying on an absolute address.

Pseudocode:

```text
scan the game module for a uniquely identifying instruction sequence
assert exactly one match
reserve nearby executable storage
save the displaced instruction bytes
redirect the original site to replacement storage
replacement logic performs one narrow operation
replay every displaced instruction with original semantics
jump to the first untouched instruction
on disable, restore saved bytes, unregister the match, free storage
```

Required independent facts: signature uniqueness, instruction boundaries, continuation address, register/flag liveness, and whether the site executes on the expected thread.

## Pattern B — captured object pointer

Purpose: expose fields of the object most recently observed by a discovery event.

Pseudocode:

```text
at a verified object-use site:
    validate the candidate object pointer
    publish it to a private pointer cell
    continue original execution
table records read typed fields relative to that pointer
invalidate or refresh the cell when the object is destroyed/replaced
```

Never assume that a pointer remains valid after moving an item, closing a menu, changing zones, or reloading a save.

## Pattern C — calculation scalar override

Purpose: alter one multiplier or bounded scalar while leaving the surrounding state model intact.

Pseudocode:

```text
if feature_enabled and input_is_valid:
    substitute the independently chosen scalar
else:
    use the original scalar
preserve original data flow and all live machine state
```

This is appropriate only after proving the site is a calculation and not a canonical save write.

## Pattern D — decrement suppression

Purpose: prevent a loss operation such as damage, durability, oxygen, or a timer decrement.

Pseudocode:

```text
identify the exact loss event
verify the feature applies only to the intended resource
skip or neutralize the decrement
preserve unrelated validation, events, UI refresh, and persistence logic
```

The same visible result can arise from a cached display edit, so dynamic evidence is mandatory.

## Pattern E — table-interface orchestration

Purpose: connect controls, hotkeys, slots, and lifecycle actions to low-level records/hooks.

Pseudocode:

```text
on enable: initialize controls and dependencies
on user action: validate feature state and pointer freshness
perform one bounded read/write
on disable: stop callbacks, clear transient state, restore hooks
```

Lua/UI logic is not a substitute for pointer validation or transactional rollback.

## Pattern F — position slot manager

Purpose: save and load player positions in manual or dynamic slots.

Pseudocode:

```text
save: capture a validated local-player transform plus required context
load: verify player and world context, then apply transform conservatively
delete: remove only the selected slot data
```

The required context may include world/cell identity, stance, collision state, or streaming readiness; it must be discovered, not guessed.

## Lifecycle checklist

Every independent implementation should have: one owner for each allocation, explicit dependency order, exact original-byte restoration, symbol cleanup, pointer invalidation, disable-time callback quiescence, and a test proving a second enable does not duplicate hooks.

## Risk taxonomy

| Risk | Detection |
|---|---|
| Invalid/stale pointer | Guarded reads, object lifetime tracing, zone/reload tests |
| Instruction-boundary error | Disassembly and byte-length audit |
| Register/flag corruption | Compare pre/post state and branch outcomes |
| Stack misalignment | Verify calling convention and aligned call sites |
| Save corruption | Backup, diff, reload, and new-world tests |
| World-state corruption | Disposable world and multiplayer/host tests |
| Incomplete disable | Byte comparison, symbol/allocation enumeration, restart test |
