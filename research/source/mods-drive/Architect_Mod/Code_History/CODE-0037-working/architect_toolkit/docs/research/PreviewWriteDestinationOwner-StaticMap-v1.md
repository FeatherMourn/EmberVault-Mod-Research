# CODE-0007 — returned-pointer ownership and lifetime map

This is an offline/static-only analysis of Enshrouded revision 1076226. The
supported executable SHA-256 is
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
No process access, debugger, hook, injection, executable write, or game-memory
write is authorized.

## Function boundaries and contracts

`0x3E5480` is `.pdata`-covered by `0x3E5480..0x3E5604` and calls
`0x3ED1A0` at `0x3E5578`. At that call, `RCX=[RDI+0xD8]`,
`RDX=[RDI+0xE0]`, `R8B=5`, and `R9D=EBX` (the incoming `R8D` to
`0x3E5480`). The returned `RAX` is copied to `RDX` at `0x3E5580` and is
written through until `0x3E55E6`.

`0x3ED1A0` is a split `.pdata` function. Its adjacent chunks are
`0x3ED1A0..0x3ED1DB`, `0x3ED1DB..0x3ED296`, and the cold failure path
`0x3ED296..0x3ED2B8`. It receives an owner-like object in `RCX`, a secondary
bookkeeping object in `RDX`, a byte flag in `R8B`, and a 32-bit value in `R9D`.

Other direct `0x3ED1A0` callers are `0x3E262B`, `0x3E2919`, and `0x3E52BD`.
They use the same owner fields (`+0xD8/+0xE0`) with flags `1`, `6`, and `0`,
respectively, and immediately write different subsets of the returned record.

## Returned-pointer source

The returned pointer is classified `OWNER_ROOTED_CONTAINER_SLOT`:

1. `0x3ED1A0` copies incoming `RCX` to `RDI`.
2. It passes `LEA RCX,[RDI+0xA10]` to `0x7AEDA0` (`0x3ED23D`), which returns
   the pointer in `RAX`.
3. It compares `[RDI+0xA28]` with `[RDI+0xA38]` and calls `0x3EDDE0` when they
   meet, indicating owner-rooted growth/capacity handling.
4. It uses `[RDI+0xA3C]` as a stride to derive an element index and records
   that index through an RDX-relative bookkeeping slot.
5. It clears the returned element and initializes `+0x48` from `R9D` and
   `+0x4C` from `R8B`.

This rules out a direct stack-local or RIP-relative global alias. Whether
`0x7AEDA0` reuses an existing slot or allocates storage is not proven, so the
allocation mechanism remains `UNKNOWN`.

## Writes through the returned pointer

`0x3E5480` writes 11 fields at returned offsets `+0x00`, `+0x08`, `+0x10`,
`+0x14`, `+0x1C`, `+0x20`, `+0x28`, `+0x2C`, `+0x34`, `+0x38`, and `+0x3C`.
The `+0x00` pointer is loaded from its input record (`[RSI]`; on the
`0x3EB810` path this is `[acceptedElement+0x48]`). The remaining values are
copied from stack temporaries populated by `0x8CD2C0` and are classified as
derived transform/state values; their semantic names are intentionally not
invented.

## Per-candidate and lifetime conclusions

Within one `0x3EB810` invocation, `RCX=RBP` is held constant when calling
`0x3E5480`, so the owner and secondary bookkeeping roots are shared across
candidate iterations. The candidate-derived input at `[RSP+0x90]` varies by
element. The owner storage index calculation supports separate slots per
allocation, but allocator reuse/allocation semantics are not proven. There is
no post-loop read of these returned records in `0x3EB810`; only the Boolean
success result is consumed. No “last candidate wins” conclusion is made.

No instruction-backed reader was found connecting these writes to preview
state, `0x3E2CD0`, the `[RSI+0xF0]` cache, `[RSI+0x110]` candidate source, or
`CreateBuildingItemAction`. The result is therefore
`PERSISTENCE_UNRESOLVED` / `PARTIAL_STATIC`, not a preview-authority claim.

See `bridge/preview_write_destination_owner_static_map.json` for complete
instruction rows, call-site contracts, writes, negative findings, and safety
flags.
