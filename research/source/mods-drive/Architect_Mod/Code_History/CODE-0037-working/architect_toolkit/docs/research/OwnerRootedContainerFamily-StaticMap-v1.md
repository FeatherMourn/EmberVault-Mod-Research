# CODE-0008 — owner-rooted container family

Offline/static-only analysis for Enshrouded revision 1076226
(`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`).
No process access, debugger, hook, injection, executable write, or game-memory
write was performed.

## Direct contracts

All four direct `0x3ED1A0` call sites are validated in the machine-readable
map:

| Call site | RCX | RDX | R8B | R9D |
| --- | --- | --- | --- | --- |
| `0x3E262B` | `[R14+0xD8]` | `[R14+0xE0]` | `1` | `EBX` |
| `0x3E2919` | `[RSI+0xD8]` | `[RSI+0xE0]` | `6` | `EDI` |
| `0x3E52BD` | `[R14+0xD8]` | `[R14+0xE0]` | `0` | `EDI` |
| `0x3E5578` | `[RDI+0xD8]` | `[RDI+0xE0]` | `5` | `EBX` |

The differing `R8B` constants support a discriminator/record-kind role, but
no semantic name is assigned. `R9D` is copied into returned-slot `+0x48`; its
key/index/generation meaning is unresolved.

## Container and allocation behavior

`0x3ED1A0` treats incoming `RCX` as an owner root and incoming `RDX` as a
secondary bookkeeping root. The owner storage/control object is at
`ownerRoot+0xA10`; owner fields `+0xA28/+0xA38` are compared for a growth
condition and `+0xA3C` supplies an element stride. Secondary metadata uses
`RDX+0x100`, `RDX+0x108`, and RDX-relative index slots.

The helper at `0x7AEDA0` is statically classified as
`FREE_LIST_REUSE_OR_BOUNDED_APPEND`: a nonzero control-block `+0x10` pops a
free-list element, otherwise `[+0x30] < [+0x28]` appends at
`[+0x00] + index*[+0x2C]`; exhaustion returns null. Counters at `+0x18`,
`+0x1C`, and `+0x20` are updated. `0x3EDDE0` is a connected bucket and
bookkeeping growth path: it drains/cleans entries, allocates new bucket
bookkeeping through `0x263470`, resets `+0x100/+0x108`, and increments the
owner bucket count at `+0xA08`.

## Returned slots and convergence

`0x3E5480` writes eleven returned-slot fields. On the `0x3EB810` path, the
owner root is constant across candidate iterations while the input pointer
`[RSP+0x90]` is `[acceptedElement+0x48]`. The allocator can reuse or append
slots, but no post-loop reader retains a winner; only the Boolean result is
consumed.

Anchored reads/writes are limited to the direct family and its allocator/growth
helpers. No instruction-backed reader connects these slots to preview state,
`0x3E2CD0`, `[RSI+0xF0/+0x110]`, `CreateBuildingItemAction`, or VoxelBlueprint
identity. Ownership/lifetime is therefore `PERSISTENCE_UNRESOLVED`, and the
overall result is `PARTIAL_STATIC` rather than a preview-authority claim.

See `bridge/owner_rooted_container_family_static_map.json` for full disassembly,
`.pdata` chunks, call windows, evidence labels, negative findings, and safety
gates.
