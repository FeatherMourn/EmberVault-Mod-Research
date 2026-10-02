# Architect Semantic Action Observer v0.18.0

## v0.17 live promotions

The controlled 37 → 13/24 → move 13 → move 24 → merge 37 run produced four
correlated destination operations with zero drops. Empty destinations changed
from zero to ItemId `631520303` with counts 24, 13, and 24. The merge destination
changed from count 24 to 37 with transfer amount 13. R14 was stable and readable,
and `[R14+0]` equaled `631520303` throughout.

The following are now **PROVEN_BUILD_1076226**:

- R15 is the destination `keen::ItemStack*` on these validated paths.
- `[rsp+0x88]` is the transferred amount.
- `0x3884E3` observes completed empty-destination initialization.
- `0x38859F` observes the resulting merged destination count.
- R14 is readable and its first dword equals the transferred ItemId.

R14's concrete type, inventory ownership, and InventoryTransferAction remain
unresolved. The latest placement evidence—one commit, two records, 31 ms,
thread 24292 shared with inventory activity—is recorded without assigning a
side identity.

## Recovered target prototype

The evidence-supported temporary prototype for `0x3883C0` is:

```text
result candidateOperation(
    candidateArg1Result*,
    candidateArg2InventoryAccessContext*,
    packed InventorySlotId candidateArg3DestinationSlot,
    candidateArg4ResolverRecord*,
    uint32 candidateArg5Raw,
    uint32 transferAmount)
```

RCX is a result/status object. RDX is copied to RBP and feeds inventory lookup
helpers. R8 is copied to RBX and decoded as a packed slot value. R9 is copied to
R14. Caller stack `+0x20` becomes EDI and remains semantically unresolved.
Caller stack `+0x28` is the proven transfer amount.

R14 originates from resolver `0xCB4B50` in all three observed paths. The wrapper
returns an existing record whose first dword is ItemId, but static provenance
does not establish a concrete ItemInfo type; `R14ConcreteTypeStatus` therefore
remains **UNSOLVED**.

## Slot and ItemStack derivation

Helper `0xCBE2B0` decodes its R8 qword into a low EntityId-compatible dword and
a high slot-index byte. Both lookup paths reject slot indices ≥8.

Destination helper `0x387830` decodes candidateArg3, obtains an inventory block,
then computes:

```text
rcx = slotIndex + slotIndex*2
destination = inventoryBase + rcx*4
            = inventoryBase + slotIndex*0x0C
```

Source helper `0x386C00` decodes the other caller slot and invokes `0xCB4EE0`.
That helper independently validates slot <8 and computes the same
`base + slotIndex*0x0C` address. This is machine-code derivation, not address
rounding.

Caller `0x385D80` receives two packed slot values in R8/R9, resolves their stack
pointers through `0x386C00`, and preserves them at `[rbp-0x40]` and
`[rbp-0x30]`. For returns `0x3860AC` and `0x38613F`, destination uses caller RDI
and the source candidate is `[callerRbp-0x30]` associated with caller RBX.

Caller `0x386180` likewise resolves caller R9/RDI to saved R15 and caller R8/RBX
to saved R14. At return `0x38636A`, destination uses RBX/R14 and the source
candidate is RDI/R15.

This is sufficient to add source-candidate pre-state observation without three
new call-site hooks. The existing `0x388453` shim can read the callee's saved
nonvolatile caller registers and, only for the three exact return RVAs, the
validated caller local. This materially reduces hook surface.

The v0.18 record reports both packed slot candidates, decoded fields, stack
pointers, and code-derived bases. `addressEquationMatches` verifies each
captured pointer equals its derived base plus slotIndex×0x0C. These are
InventorySlotId-compatible candidates pending repeat live validation; entity
ownership remains **UNSOLVED**.

## Source observation boundary

The source candidate is copied only as three dwords before destination work.
The existing post shims also snapshot it when destination work completes.
That latter point is still inside `0x3883C0`, before control returns to callers;
later caller-side source mutation is not claimed. Consequently source identity
and pre-state are **EXPERIMENTAL**, and a true final source post-state remains
**UNSOLVED** until live evidence or an independently safe caller completion
point proves it.

No additional call-site hooks were installed. No arbitrary memory search,
recursive dereference, game call, action submission, or mutation was added.

## Controlled caller roles

- `0x38636A`: `observed_during_split`
- `0x38613F`: `observed_during_move_to_empty`
- `0x3860AC`: `observed_during_existing_stack_merge`

These labels describe the controlled run only; they are not universal function
names. The full bounded machine report is
`bridge/inventory_move_caller_scan.json`.

## Exact live test

1. Start v0.18.0 in a disposable world and confirm a fresh session ID, all
   inventory probe hooks installed, zero drops, and InventoryTransferAction
   still UNSOLVED.
2. Use one terrain-stone stack with exactly 37 items and avoid unrelated
   inventory activity.
3. Split it into 13 and 24.
4. Move the 13 stack once.
5. Move the 24 stack once.
6. Merge them back to 37.
7. Preview/cancel one building placement, then commit one placement.
8. Stop through the normal native stop workflow and wait for clean unload.

Return exactly:

- `bridge/semantic_actions.jsonl`
- `bridge/semantic_action_status.json`
- `bridge/native_runtime.log`
- `bridge/native_status.json`
- `bridge/building_capture.json`
- `bridge/upstream_trace.json`

Static research artifacts are `bridge/inventory_move_pointer_site_scan.json`
and `bridge/inventory_move_caller_scan.json`.
