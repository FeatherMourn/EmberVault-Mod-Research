# Item Observer Behavior-First Stack Amount Discovery v7

> Performance note: v7.1 replaces per-hit broad-scan context collection with a
> staged fast-scan/comparison/targeted-context pipeline. See
> `ITEM_OBSERVER_STACK_DIFFERENTIAL_RESEARCH_V7_1.md`. The research method and
> safety boundaries below remain unchanged.

## Proven

The v6 descriptor capture found 4,642 exact references: 2,228 each for RVAs
`0x160BFC0` and `0x1857610`, and 93 each for `0x1908FB0` and `0x18BAFA0`.
Every reference is ordinary file-backed relocated `.rdata`; there are zero owner
candidates, pointer chains, and runtime objects. Its corrected state is
`STATIC_REFERENCES_ONLY`.

**ACTION STRING / DESCRIPTOR PATH — DEPRIORITIZED.** The names lead into generic
descriptor/type metadata rather than actionable inventory-operation state.
Existing descriptor tools and reports are preserved.

## Test session

`Invoke-StackAmountDifferentialCapture.ps1` creates a new session whenever a
baseline is captured (unless an explicit session ID selects another session).
Each one-shot capture has a UUID, UTC timestamp, label, sequence, executable
fingerprint, requested values, region statistics, candidates, and bounded
`±0x40` context. Files are retained beneath
`bridge/item_observer_stack_sessions/`; the deterministic session index is
`bridge/item_observer_stack_session.json`.

The scan includes only committed, writable, non-executable `MEM_PRIVATE` and
`MEM_MAPPED` regions with `PAGE_READWRITE` or `PAGE_WRITECOPY`. It searches
aligned `uint32`/`int32` representations in-place. `uint16` is opt-in with
`-IncludeUInt16`. It does not dump regions.

## Baseline

With Enshrouded running and a known uncommon stack of 37:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackAmountDifferentialCapture.ps1 -Label baseline -Values 37
```

Record the printed session ID from `bridge/item_observer_stack_session.json` if
multiple sessions might be interleaved. `NO_BASELINE_CANDIDATES` is a valid
negative result.

## Split result

Split the stack using only the vanilla UI, for example into 13 and 24, then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackAmountDifferentialCapture.ps1 -Label split -Values 13,24
```

The quantities are parameters, not scanner constants.

## Move result

Move one split stack to another slot without changing its amount, then capture
both known amounts so stable, copied, and relocated candidates remain visible:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackAmountDifferentialCapture.ps1 -Label move -Values 13,24
```

## Merge result

Merge through the vanilla UI and capture the restored quantity:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackAmountDifferentialCapture.ps1 -Label merge -Values 37
```

Then compare the latest capture for each phase:

```powershell
python tools\ItemObserver\compare_stack_captures.py
```

The comparison is written to `bridge/item_observer_stack_comparison.json`.

## Candidates

The comparator reports raw scoring reasons and classifications including
`VALUE_TRACKED_IN_PLACE`, `ORIGINAL_OBJECT_CHANGED`, `NEW_OBJECT_APPEARED`,
`OBJECT_MOVED`, `DUPLICATE_VALUE_AMBIGUOUS`, and candidate disappearance.
It does not require the original address to survive a split or move.

## Candidate object context

Each retained candidate includes its address, region base/type/protection,
integer width and representations, exact value, raw bounded context, and both
raw and amount-normalized SHA-256 context fingerprints. Matching normalized
contexts at different addresses are reported as structural `OBJECT_MOVED`
correlations. This is bounded observation, not recursive pointer traversal.

## Inferred

A same-address value transition followed by amount stability during a slot move
would favor a persistent object. A context-correlated address change would favor
relocation or slot/container-owned storage. These remain inferences until at
least two controlled sessions with different quantities reproduce them.

## Disproven

The descriptor experiment did not find a writable runtime owner or inventory
consumer. It does not disprove every possible future descriptor use, only its
current value as the primary bridge.

## No-hook decision

No hook is authorized or installed. The capture uses only
`PROCESS_QUERY_INFORMATION | PROCESS_VM_READ`, `VirtualQueryEx`, and
`ReadProcessMemory`; it does not inject, patch, guard, breakpoint, or alter page
protection.

## No-mutation decision

The Toolkit writes no process memory and performs no inventory action. The
player performs split, move, merge, and any optional consume/drop action through
vanilla Enshrouded UI.

## Next research step

After two reproducible sessions identify a strong candidate, proceed to
read-only Live Stack Object Characterization v8: object lifetime, candidate
amount field, possible item-identity field, slot/container relationship, and
bounded pointer ownership. If duplicates remain, add one vanilla single-step
discriminator (such as 37 to 36). If no integer candidate exists, investigate
packed, serialized, indirect, or authoritative remote representation from the
negative evidence rather than guessing.
