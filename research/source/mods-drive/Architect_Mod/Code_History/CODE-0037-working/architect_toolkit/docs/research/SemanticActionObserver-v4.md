# Architect Semantic Action Observer v0.17.0

## Evidence update

The v0.16 session produced five readable candidate pointers with no drops:
`P0`, `P0+0x0C`, `P0+0x60`, `P0+0x6C`, then the last pointer again. The final
pointer changed from all-zero dwords to ItemId `631520303`, count `24`, pide
`0`. The registered item is `Build_TerrainMaterial_T1_Stone` (GUID
`8870fa83-04e6-4b5a-ac2a-ea13205ce469`). Together with the reflected
`keen::ItemStack` size `0x0C` and `Inventory` size `0x60` (eight ItemStacks),
this proves R15 is a live pointer to a structure matching ItemStack at this
validated path and build.

The relative topology is consistent with adjacent ItemStack positions and two
corresponding positions separated by one Inventory-sized block. Ownership,
EntityId, and slot identity remain **UNSOLVED**; no address rounding is used to
invent an owner.

The v0.16 placement result is preserved unchanged: preview/cancel emitted no
BuildingPlaceEvent and one commit emitted two raw events with one logical ID.
Inventory probing and candidate side 1 both occurred on thread 11612 in that
session, but this provides no client/server identity.

## Dynamic caller analysis

All three live return RVAs are returns from exact direct calls to `0x3883C0`.
The bounded machine report is `bridge/inventory_move_caller_scan.json`.

| Return RVA | Enclosing function | Call setup and bounded evidence |
| --- | --- | --- |
| `0x38613F` | `0x386044..0x386166` | Call at `0x38613A`; RCX=`&[rbp-0x48]`, RDX=R15 context, R8=RDI, R9=resolver return; sixth argument is EBX. Success adds EBX to R12D. |
| `0x38636A` | `0x386264..0x386388` | Call at `0x386365`; RCX=`&[rsp+0x30]`, RDX=RBP context, R8=RBX, R9=resolver return; sixth argument is R13D after comparisons/conditional minima at `0x3862FA..0x38630C`. |
| `0x3860AC` | `0x386044..0x386166` | Call at `0x3860A7`; RCX=`&[rbp-0x48]`, RDX=R15 context, R8=RDI, R9=resolver return; sixth argument is R12D. Success writes R12D to an output count-like field. |

After its prologue, `0x3883C0` observes that sixth caller argument at
`[rsp+0x88]`. The empty path loads it at `0x3884C5` and writes it to
`[r15+4]` at `0x3884D0`. The existing-item path loads it at `0x388542`, bounds
the applied value, and adds the bounded value to `[r15+4]` at `0x38859F`.
This makes `candidateAmountRaw` strongly **INFERRED**, pending direct live
agreement with 13/24/37 transitions.

The callee copies R9 to R14. These observed callers supply a resolver return,
and the callee reads `[r14]` as an item identity plus other distant fields.
That is consistent with an ItemInfo/definition record, but R14 identity remains
**UNSOLVED** until live values resolve coherently against the catalog.

No caller is named split, move, or merge solely from its timing.

## InventoryMovePointerProbe v2

The original pre-state hook at `0x388453` remains build-locked. It additionally
captures guarded dwords from `[rsp+0x88]` and `[r14]`, plus the raw R14 pointer.
No recursive dereference is performed.

Two post-state sites are statically complete and uniquely validated:

- Empty initialization: RVA `0x3884E3`, after ItemId/count/pide writes and the
  existing `0x387F80` call. The 13 overwritten bytes are whole exit
  instructions and are replayed before capture.
- Existing-item merge: RVA `0x38859F`. Its 12-byte block begins with the only
  count mutation (`add [r15+4],r12d`). The shim replays the add, captures the
  post-state, then preserves the original flag write, comparison, and both
  branches.

Each post hit finds only a recent same-thread, same-pointer pre-event within one
second and emits a separate correlated operation record containing both pre and
post dwords, raw amount, caller return RVA, and path classification. Failure to
validate either exact post byte sequence leaves post hooks disabled; the proven
pre-state hook remains independently fail-closed.

Hook-thread work is limited to bounded guarded reads and ring publication. No
file I/O, ItemStack write, new game call, inventory submission, resolver hook,
selector trampoline, or broad scan is introduced.

## Classification ledger

| Claim | Classification |
| --- | --- |
| BuildingPlaceEvent mapping | **PROVEN** |
| Semantic publication on revision 1076226 | **PROVEN** |
| R15 live ItemStack pointer at this path | **PROVEN** |
| R15 specifically represents the destination ItemStack | **INFERRED**, pending v2 pre/post results |
| `[rsp+0x88]` is an operation amount | **INFERRED**, pending live values |
| R14 is ItemInfo/definition | **UNSOLVED** |
| Inventory ownership or slot identity | **UNSOLVED** |
| InventoryTransferAction execution point | **UNSOLVED** |

## Exact short test

1. Start v0.17.0 in a disposable world. Confirm a fresh `sessionId`, pre-hook
   and post hooks installed, zero drops, and InventoryTransferAction UNSOLVED.
2. Use only one known terrain-stone stack with visible count 37.
3. Split 37 into 13 and 24.
4. Move the 13 stack once.
5. Move the 24 stack once.
6. Merge back to 37.
7. As a placement regression, preview/cancel once and commit one ordinary
   Construction Hammer placement.
8. Stop through the normal native stop workflow and wait for clean unload.

Return exactly:

- `bridge/semantic_actions.jsonl`
- `bridge/semantic_action_status.json`
- `bridge/native_runtime.log`
- `bridge/native_status.json`
- `bridge/building_capture.json`
- `bridge/upstream_trace.json`

Static reports retained locally are `bridge/inventory_move_pointer_site_scan.json`
and `bridge/inventory_move_caller_scan.json`.
