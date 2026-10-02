# Architect Semantic Action Observer v0.20.0

## Outcome

v0.20 incorporates the four-operation v0.19 live capture and promotes the
InventoryTransferAction consumer, its 0x20 payload, target-slot mapping, and
candidate consumed-version tracking to **PROVEN_BUILD_1076226**. The concrete
owner types, dispatch producer, and general EntityId ownership remain
**UNSOLVED**.

The existing v0.18 source identity at return `0x38613F` is **DISPROVEN**. RBX
there is the effective transfer count (13 and 24 in the live capture), not a
packed InventorySlotId. v0.20 never decodes it as a slot.

## Correct source path

The general handler receives source InventorySlotId in R9 and target in R8:

```text
R9 source slot -> RBX -> call 0x386C00 at 0x385DCD
                         success result pointer at [RBP-0x30]
R8 target slot -> RDI -> call 0x386C00 at 0x385DDC
                         success result pointer at [RBP-0x40]
```

At `0x38613A`, `[RBP-0x30]` remains the game's resolved source ItemStack
pointer, while `mov [RSP+0x28],EBX` supplies the effective count to the
destination primitive. v0.20 takes source identity from the independently
captured, same-thread action and the pointer only from `[RBP-0x30]`. For type 2
the correlation deliberately accepts raw action amount zero; for type 3 it
requires action amount to equal the downstream effective amount.

This corrects the controlled `6650:5` and `6650:6` identities on the
`0x38613F` route. The snapshot available at the destination primitive occurs
after the handler's source-side operation and is therefore an intermediate
observation, not sourcePre or a claimed final sourcePost. No additional hook
was added because a safe pre/post detour was not independently live validated.

## Entity and inventory resolution

The bounded static path through `0x386C00` is:

1. `0xCBE2B0` decodes the packed slot into entity-compatible and slot fields.
2. The inventory-access context supplies an ECS/world-like root at `+0x00` and
   a primary component/access object at `+0x20` (with a fallback at `+0xA8`).
3. `0x8D3630` transforms/obtains lookup context.
4. `0x8C72A0` (or fallback `0x8C70F0`) resolves the entity-compatible key and
   returns an existing inventory-compatible object pointer.
5. `0xCB4EE0` applies the decoded slot index and yields the ItemStack pointer.

This proves the code path and the final 0x0C ItemStack stride. It does not prove
the concrete names of the intermediate ECS/component types, so inventory
ownership is not promoted. Session-local addresses are never hard-coded.

## Correlation and version behavior

Ring correlation no longer depends on a record's pending-writer flag, so the
worker cannot make a valid action unavailable before the downstream hook. All
type-2 and type-3 downstream pre/post records inherit the action sequence as a
nonzero neutral operation ID. The candidate consumed-version after-read uses
the same retained record identity. The observed before/action sequence
`0 -> 3447 -> 3752 -> 3857 -> 4126` proves tracking behavior, not owner type.

The analyzer reports `actionAmountRaw` separately from
`effectiveTransferAmount`. Type 3 equality is validated; type 2 raw zero with a
nonzero downstream full-stack count is supported rather than contradicted.

## Stale-report prevention

`runtime/Stop-ArchitectNative.ps1` requests normal shutdown, waits until all
semantic hooks are removed and clean stop is reported, then invokes the offline
analyzer. Analyzer failure is reported independently and cannot affect game or
runtime state. Generated reports include generation time and the analyzed
current session ID.

## Exact live test

In a disposable world, start v0.20 and use one stack of 37:

1. Split to 13 and 24.
2. Move the 13 stack to an empty slot.
3. Move the 24 stack to the other observed inventory.
4. Merge 13 into 24 to restore 37.
5. Run `runtime\Stop Architect Native.bat` and wait for the fresh report.

Verify four nonzero shared operation IDs, source identities `6650:5`, `6650:5`,
`6650:6`, `6650:4`, exact target mappings, type-3 24/24 amount equality,
type-2 raw-zero/effective 13,24,13 behavior, and the consumed-version chain.

Return exactly:

- `bridge/semantic_actions.jsonl`
- `bridge/semantic_action_status.json`
- `bridge/native_runtime.log`
- `bridge/native_status.json`
- `bridge/building_capture.json`
- `bridge/upstream_trace.json`
- `bridge/analysis/latest_semantic_capture_report.json`
- `bridge/analysis/latest_semantic_capture_report.md`

No inventory, action, version, selector, registry, or world memory is written.
