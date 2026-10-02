# InventoryTransfer Static Map v1

## Scope and build lock

This report is an offline-only analysis of Enshrouded revision 1076226,
SHA-256 `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
The executable was read as a PE file; no process was launched or opened, and no
runtime or executable file was changed.

## Strongest result

The region beginning at `0x371810` is the first **PROVEN** native consumer of
an `InventoryTransferAction`-shaped payload connected to the validated
ItemStack mechanics. It obtains an envelope pointer from `[RDX+0x10]` and the
payload begins at `RSI+0x08`. Every reflected field is used at the corresponding
payload-relative offset:

| Payload offset | Machine access | Downstream use | State |
| --- | --- | --- | --- |
| `+0x00` | `[RSI+0x08]` dword | copied to a consumed-record-like field | **PROVEN** access/flow |
| `+0x04` | `[RSI+0x0C]` dword | source-side identifier-like validation/lookup | **PROVEN** access |
| `+0x08` | `[RSI+0x10]` dword | target-side identifier-like validation/lookup | **PROVEN** access |
| `+0x0C` | `[RSI+0x14]` qword | source packed slot argument | **PROVEN** flow |
| `+0x14` | `[RSI+0x1C]` qword | destination packed slot argument | **PROVEN** flow |
| `+0x1C` | `[RSI+0x24]` byte | operation-type branching | **PROVEN** flow |
| `+0x1D` | `[RSI+0x25]` byte | bit-gated behavior branches | **PROVEN** flow |
| `+0x1E` | `[RSI+0x26]` word | amount passed toward validated transfer calls | **PROVEN** flow |

The collective exact layout, field widths, control uses, paired-slot argument
flow, and amount flow into `0x3883C0` distinguish this from the previous broad
multi-offset candidates. The two 32-bit values are described as identifier-like
where machine code alone is being discussed; their reflected source/target
EntityId names follow from the now-complete action identity, not merely width.

## Control and data flow

```text
candidate dispatch context (RDX)
  +0x10 -> envelope (RSI)
             +0x08 -> InventoryTransferAction payload
  +0x38 -> candidate consumed-input record

0x371810..0x37229F candidate InventoryTransferAction consumer
  type == 3
    0x37200D -> 0x386180..0x3863B0 candidate type-3 handler
      0x386365 -> 0x3883C0 validated destination ItemStack primitive
  accepted non-3 path
    0x372020 -> 0x385D80..0x386166 candidate general move handler
      0x3860A7 -> 0x3883C0 validated merge-observed path
      0x38613A -> 0x3883C0 validated empty-move-observed path
```

PE unwind entries split the two handlers into several fragments. The ranges
above are logical code extents; the precise fragments are recorded in
`bridge/inventory_transfer_static_map.json`.

At both calls from the consumer, action `+0x0C` is placed in R9 and action
`+0x14` in R8. `0x385D80` and `0x386180` preserve both packed values, resolve
their ItemStack addresses through `0x386C00`, and ultimately pass the destination
value in R8 to `0x3883C0`. This independently agrees with the v0.18 source and
destination derivation. The word at action `+0x1E` is used as the operation
amount on the type-3 route; the general route also supplies it to its specialized
branch before reaching the primitive.

The full direct-call inventory found nine callers of `0x385D80`, three callers
of `0x386180`, and fourteen callers of `0x3883C0`. The action consumer is the
only inspected shared caller that presents the exact complete 0x20-byte action
layout. No direct rel32 caller or direct absolute pointer to `0x371810` was
found, so the next higher dispatch edge remains **UNSOLVED** and is likely
indirect or table-driven. “Likely” is an inference, not an identified mechanism.

## Versioned input and consumption

At entry:

- `0x37182C`: `RSI = [RDX+0x10]`;
- `0x371842`: `EAX = [RSI+0x08]`, action payload `+0x00`;
- `0x37184D`: `RCX = [RDX+0x38]`;
- `0x371869`: `[RCX+0x20] = EAX`.

This proves a version-like dword is copied into a second record before action
processing. Its structural agreement with reflected `VersionedData` and
`consumedInventoryTransferAction` makes consumed-version publication
**INFERRED**. The executable evidence gathered here does not yet prove that
RDX is concretely `ClientPlayerInput`, that its `+0x38` pointee is concretely
`ServerConsumedPlayerInput`, or that `+0x20` is the named consumed field.
No separate comparison against an old consumed version was found in this
bounded region; only the update/copy is proven.

## R14 provenance

All three validated primitive calls obtain the pointer passed as R9, and copied
to R14 by `0x3883C0`, from `0xCB4B50`. That resolver:

1. rejects a zero dword key;
2. selects a container at owner `+0x38`;
3. performs a key lookup through `0xCA5BC0`;
4. dereferences and returns the stored record pointer.

Existing population analysis at `0xCE79C0..0xCE8120` shows an owner `+0x38`
Item-ID-to-pointer container populated with records returned by typed
`keen::ItemInfo` resource resolution, with record `+0x00` copied as the key.
Together with live `[R14+0] == transferred ItemId`, this supports
“ItemInfo-compatible resolved record pointer” as **INFERRED**. It is not promoted
to a concrete `ItemInfo*` because this pass did not statically tie the exact
runtime owner instance supplied by the inventory handlers to a particular
registry-population invocation.

## Caller-role differentiation

The action type byte explains the largest structural distinction:

- type `3` selects `0x386180`, which contains the call at return `0x38636A`
  observed during the controlled split operation;
- the alternate accepted route selects `0x385D80`, whose cold fragment contains
  returns `0x3860AC` and `0x38613F`, observed during merge and empty-slot moves.

Within the general handler, different branches select amounts and destination
conditions before the two calls. This explains why the controlled operations
landed at different return RVAs. It does not prove those call sites are exclusive
to split, merge, or empty-slot moves, so exclusivity remains **UNSOLVED**.

## Rejected hypotheses

- `0x8FA60..0x8FB30` is **DISPROVEN** as this consumer: `+0x1E` is byte-sized,
  unrelated offsets dominate, and no flow reaches the validated primitive.
- `0xC9609..0xC96FE` is **DISPROVEN**: it is consistent with generic
  reflection/field traversal and lacks inventory argument provenance.
- `0x389136..0x389222` is **DISPROVEN**: it is a stack-deletion logging/error
  path, not transfer dispatch.
- Metadata clusters `0x19ECB30` and `0x1A13580` remain **EXPERIMENTAL** as
  registration evidence. They corroborate the reflected name but still expose
  no direct executable handler pointer or xref.
- A direct rel32 caller into `0x371810` is **DISPROVEN** for this build.

## Remaining boundary

The action payload and its path into the validated inventory mechanics are now
**PROVEN**. Still **UNSOLVED** are the producer that fills the envelope, the
indirect registration/dispatch mechanism, concrete types for the two context
objects, the named ownership of the consumed-version destination, exact runtime
ownership of the two inventory EntityIds, and exclusive semantics for each low
level call site.

## Recommended next live experiment (not performed)

After an independent safety review, add one build-locked, observe-only capture
at the `0x371810` consumer entry—not at the lower primitive. Capture only the
0x20-byte payload at `([RDX+0x10] + 0x08)`, the destination version dword at
`[[RDX+0x38]+0x20]` before/after, thread ID, and return address. Repeat the
controlled 37 → split 13/24 → empty moves → merge sequence and correlate the
payload slot IDs and amount with existing v0.18 records. Do not dereference
identifier fields, mutate the payload, or assign client/server roles from thread
identity.

## Reproduction

```powershell
python tools/ItemObserver/scan_inventory_transfer_static_map.py
python -m unittest tools.ItemObserver.test_inventory_transfer_static_map -v
python tools/run_offline_regression.py
```
