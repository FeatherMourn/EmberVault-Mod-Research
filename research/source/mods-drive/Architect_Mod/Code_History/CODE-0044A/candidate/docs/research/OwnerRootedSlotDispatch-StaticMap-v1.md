# CODE-0009 — Owner-rooted slot dispatch (offline static map)

Status: `PARTIAL_STATIC`, `OFFLINE_STATIC_ONLY`, build locked to Enshrouded
revision `1076226`, executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.

This milestone reads only the on-disk executable. It installs no hooks, opens
no process, and writes neither game memory nor executable memory.

## Slot allocation and initialization

`0x3ED1A0` is a chained `.pdata` function with ranges
`0x3ED1A0–0x3ED1DB`, `0x3ED1DB–0x3ED296`, and cold range
`0x3ED296–0x3ED2B8`. It copies incoming `RCX` to the owner root (`0x3ED1B2`),
passes `owner+0xA10` to `0x7AEDA0` (`0x3ED23D`), then clears the returned slot
with five 16-byte `MOVUPS` stores (`0x3ED24A–0x3ED25C`). The initializer then
stores incoming `R8B` at slot `+0x4C` (`0x3ED260`) and incoming `R9D` at slot
`+0x48` (`0x3ED266`). The secondary index is written at `0x3ED27E` after
division by the owner stride `[owner+0xA3C]`.

The four direct allocator callers remain the known contracts:

| call RVA | R8B | R9D | owner/secondary setup |
|---|---:|---|---|
| `0x3E262B` | 1 | `EBX` | `[R14+0xD8]`, `[R14+0xE0]` |
| `0x3E2919` | 6 | `EDI` | `[RSI+0xD8]`, `[RSI+0xE0]` |
| `0x3E52BD` | 0 | `EDI` | `[R14+0xD8]`, `[R14+0xE0]` |
| `0x3E5578` | 5 | `EBX` | `[RDI+0xD8]`, `[RDI+0xE0]` |

No semantic name is assigned to either field.

## Anchored consumer/dispatcher

`0x3E5A60–0x3E5D98` is an anchored dispatcher: `RCX` is retained as owner
(`RDI`), `RDX` as a secondary root (`RSI`), and the secondary range is walked.
At `0x3E5AC2` it calls the fixed-span helper `0x3EE0C0`; that helper bounds
checks an index against `[owner+0xA38]` and returns
`[owner+0xA10] + index * [owner+0xA3C]`. The resolved slot is then in `RBX`.

The byte at slot `+0x4C` is read at `0x3E5ACA`, range checked against 9, and
dispatched through the table at `0x3E5D70`. The handler entry setup is common:
`RCX=owner`, `RDX=slot`, `R8D=[slot+0x48]`. Values 0, 1, 5, and 6 dispatch to
`0x3E2500`, `0x3E50D0`, `0x3E27B0`, and `0x3E5480` respectively (values 7/8
share the failure/exit target; value 9 targets the later inline path).

## Value-5 handler

The value-5 target is `0x3E27B0–0x3E2940`. It reads slot fields at
`+0x00,+0x08,+0x10,+0x14,+0x18,+0x1C,+0x20,+0x28,+0x2C,+0x34,+0x38,+0x3C`,
and owner fields `[RSI+0x110]`, `[RSI+0x130]`, `[RSI+0xD8]`, and `[RSI+0xE0]`.
It calls `0x87A2E0` and `0x879D70`; if successful it creates another family
slot via `0x3ED1A0` with discriminator 6 (`0x3E2919`) and stores the helper
result in that slot. This is an instruction-backed family edge, but neither
callee is statically linked here to preview/ghost state, `0x3E2CD0`, a
CreateBuildingItemAction, or VoxelBlueprint identity.

## Lifecycle

`0x7AEDA0–0x7AEDFB` (no `.pdata`, bounded by `RET`/`INT3`) proves free-list
reuse when `[control+0x10]` is nonzero and bounded append otherwise. Control
fields used are base `+0x00`, free-list head `+0x10`, counters `+0x18/+0x1C`,
operation counter `+0x20`, bound `+0x28`, stride `+0x2C`, and append index
`+0x30`; exhaustion returns zero. `0x3EDDE0` drains secondary bucket ranges,
cleans selected kind-9 entries, allocates bookkeeping, resets `+0x100/+0x108`,
and increments owner `+0xA08`. A concrete instruction that returns a slot to
the free-list head was not found, so lifetime is classified
`MIXED_LIFETIME_UNRESOLVED`.

## Convergence decision

The dispatcher and value-5 family edge are proven, but preview/ghost, snap
cache, commit (`0x3E2CD0`), CreateBuildingItemAction, and VoxelBlueprint
convergence are not. The first unresolved boundary is the semantics of
`0x87A2E0`/`0x879D70` and any later consumer of the emitted kind-6 slot.
The report therefore remains `PARTIAL_STATIC`; no runtime observer is
authorized and the branch is parked per CODE-0009 stop conditions.

See `bridge/owner_rooted_slot_dispatch_static_map.json` for the complete
instruction evidence and machine-readable contracts.
