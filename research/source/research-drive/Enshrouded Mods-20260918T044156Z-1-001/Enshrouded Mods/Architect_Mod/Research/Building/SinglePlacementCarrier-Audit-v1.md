# Single Placement Carrier — historical audit

Status: **EXPERIMENTAL / NOT PROVEN** (Enshrouded revision 1076226).

## Historical path

The earlier armed-placement experiments used the build-locked
`BuildingPlaceEvent` path (`0x3E3505 -> 0x3EBB70`) and, in some revisions,
attempted selector or resolver detours.  The resolver detour at `0xCB4B50`,
the function-entry detour at `0x3E2CD0`, and the selector trampoline around
`0x280F86` are rejected: they caused access violations or corrupted call
state.  They are not reused by v0.31.

The stable helper-entry hook receives the fifth, stack-passed tracking item
argument and forwards the original helper call.  v0.31 changes only the local
copy of that argument immediately before forwarding, after bounded validation;
it never writes the event context, resolver table, ItemInfo, or placement
transform objects.

## Assumption classification

| Assumption | Status | Evidence / limitation |
| --- | --- | --- |
| `0x3EBB70` is a stable helper entry for `BuildingPlaceEvent` | STILL_VALID | Signature and event-allocation sequence are build validated. |
| tracking item is the fifth argument | STILL_VALID | `0x3E34E1` → `0x3E34F1` → `0x3E3505` chain. |
| changing the forwarded fifth argument is upstream of helper consumers | SAFE_TO_RETEST | Function-entry interception is before helper body, but world authority is not yet proven. |
| both raw events represent one logical placement | SAFE_TO_RETEST | Repeated captures have matching transform/material signatures; semantic role remains unresolved. |
| both raw events should receive the same substitution | UNPROVEN | v0.31 applies only to a bounded matching pair and records the ambiguity. |
| child-field or resolver-table writes are required | INVALIDATED | Prior Ring experiment showed those are unnecessary for normal registered blueprints; v0.31 does not perform them. |
| selector/resolver detours are safe | OBSOLETE | Crash evidence at boot/first placement. |
| material substitution is safe | UNPROVEN | Feature remains disabled. |
| plan transforms can be replayed here | OBSOLETE FOR V0.31 | Vanilla position/orientation/bounds remain authoritative. |

## Historical drift

Current source retains legacy diagnostic bookkeeping, but selector and resolver
install flags are hard-disabled.  The new carrier state is independent and
cannot be armed by ordinary `place`; it requires an explicit experimental F8
command and a single Foundation 4m plan entry.

