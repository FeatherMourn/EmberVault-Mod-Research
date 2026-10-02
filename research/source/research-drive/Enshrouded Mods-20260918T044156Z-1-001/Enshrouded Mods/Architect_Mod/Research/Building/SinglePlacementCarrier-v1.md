# Single Placement Carrier v1

This is the first intentionally mutating milestone after the offline recorder
and editor work.  It is **EXPERIMENTAL** and must only be exercised in a
disposable test world.

## Scope and authority

The only candidate mutation is the local `trackingItemId` argument at the
validated `BuildingPlaceEvent` helper entry.  Position, orientation, volume,
owner, material, resolver tables, ItemInfo records, and context objects are
untouched.  The hook runs before the original helper body, so the argument is
connected to helper processing; whether that changes committed world geometry
is still UNSOLVED until a user confirms the placed result.

## Gates

Arming requires the supported executable fingerprint, the validated observer,
exactly one enabled plan placement, a non-empty plan identity, and desired
ItemId `950598916` (`Blueprint_Voxel_Block_Foundation_4m`).  Material mutation
is always disabled.  Every event must come from caller RVA `0x3E3505`, have a
sane context/transform, and match the original item and pair signature.

## One-shot state machine

`DISARMED -> ARMED (waiting_for_first_placement) -> CONSUMING
(placement_sequence_active) -> DISARMED`, with FAILED as a fail-closed exit.
The waiting stage lasts 10 seconds, then the short pair stage lasts 250 ms.
At most two matching raw events are accepted for one logical operation.  A new
arm replaces the previous operation; cancel, timeout, mismatch, overflow, or
unload clears the arm.

The implementation writes only the local fifth argument before forwarding and
restores the local value immediately after the original call returns.  This is
not a write to game memory.  Pair roles (client/server or authoritative side)
remain unresolved; equal transform/material signatures are the only accepted
correlation evidence.

## Diagnostics and test

`bridge/single_placement_carrier_status.json` reports state, timestamps,
operation/plan identity, raw/logical counts, result, and failure.  Semantic
records use `building_carrier_attempt` and are separate from ordinary
`building_place` records.  The analyzer treats a written argument as capture
evidence only; it never promotes that to world success.

Test in a disposable world: select one Foundation 4m plan placement, confirm
the TEST WORLD acknowledgement and “vanilla position / rotation” warning, arm
once, close F8, select a visually distinct vanilla blueprint, and commit one
placement.  Reopen F8, verify automatic disarm, and compare the resulting
geometry with the captured original and forwarded IDs.  Do not place again.

### Live result update

The wall-versus-foundation test completed inside the arm window and forwarded
and restored the Foundation ID on both raw events, but the world still placed
the wall. This proves argument substitution and disproves that this argument
alone selects committed geometry on build 1076226. The carrier mutation is
exhausted and must not be retested; future work traces the upstream
blueprint/geometry authority instead.
