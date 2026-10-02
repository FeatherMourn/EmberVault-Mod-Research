# Item Observer Incremental Tracking Research v7.2

## Current evidence

Two controlled live sessions prove numerical correlation with vanilla stack
operations. Session A contained a same-address `37 → 24 → 24 → 37` candidate.
Session B contained a candidate absent at baseline, created as 26 at split,
surviving repeated moves, and becoming 43 at merge. A later context capture no
longer held the expected value. Numerical correlation is proven; a stable stack
object is not.

## False-positive / stale-candidate lesson

An address can be a transient object, copy, cache, UI value, or allocator-reused
storage. Context captured after the experiment cannot characterize the active
object unless the candidate field still equals a phase-expected value. v7.2
therefore records `observedValueAtCapture`, `matchesExpectedValue`, and either
`ACTIVE_CANDIDATE` or `STALE_CANDIDATE` for every requested address.

## Incremental comparison

The comparator now ranks after baseline+split, again after every move, and after
merge. It emits `INCREMENTAL_COMPARISON_COMPLETED` as soon as baseline and split
are available, while listing missing later phases. `targetedContextAddresses`
contains only strong candidates present in the most recent capture, so the list
is suitable for immediate inspection rather than historical addresses.

## Multi-move support

Repeated `move` captures are preserved in sequence and named `move_1`, `move_2`,
and so on. Each same-value survival contributes independent evidence. The
comparator no longer collapses repeated labels to the last capture.

## Candidate lifecycle

Reported observational states include `BASELINE_EXISTING`, `SPLIT_CREATED`,
`VALUE_TRACKED_IN_PLACE`, `SURVIVED_MOVE`, `DISAPPEARED`, `MERGED_SURVIVOR`,
`TRANSIENT`, and `UNKNOWN`. A split-created candidate can rank strongly without
ever containing the original total at baseline.

## Immediate context capture and history

After each comparison, capture only its short address list. For a 13/24 split:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackCandidateContextCapture.ps1 -Addresses 0xAAAA,0xBBBB -Phase split -ExpectedValues 13,24
```

After a move and merge respectively:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackCandidateContextCapture.ps1 -Addresses 0xAAAA,0xBBBB -Phase move_1 -ExpectedValues 13,24
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackCandidateContextCapture.ps1 -Addresses 0xAAAA,0xBBBB -Phase merge -ExpectedValues 37
```

Every invocation creates a new timestamped file beneath
`bridge/item_observer_stack_context_sessions/<sessionId>/`. The history index is
`bridge/item_observer_stack_context_session.json`; prior snapshots are never
overwritten.

## Context differential

The comparator loads context history automatically. For repeated addresses it
reports changed byte offsets, changed aligned 4-byte and 8-byte fields, pointer
stability, allocation-base stability, and whole-context replacement. Raw bytes
remain present. Hashes separately normalize the candidate amount and obvious
pointer-like qwords. No semantic field names are asserted.

## Cross-session comparison

Keep each game-launch session separate. To compare another preserved session:

```powershell
python tools\ItemObserver\compare_stack_captures.py --additional-manifest path\to\other_session_manifest.json --additional-context-manifest path\to\other_context_manifest.json
```

Cross-session matches use lifecycle, region class/size, relative allocation
offset, and—when context history is supplied—structural fingerprints. Absolute
addresses are never expected to match across launches.

## Safety

The fast scanner remains the v7.1 bulk, single-pass implementation. Context
capture is bounded and explicitly invoked. All process operations are query/read
only: no writes, hooks, injection, page-protection changes, guards, breakpoints,
inventory mutation, save mutation, or multiplayer mutation.

## Test flow

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackAmountDifferentialCapture.ps1 -Label baseline -Values 37
# vanilla split
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackAmountDifferentialCapture.ps1 -Label split -Values 13,24
python tools\ItemObserver\compare_stack_captures.py
# immediately run context capture using targetedContextAddresses
# vanilla move
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackAmountDifferentialCapture.ps1 -Label move -Values 13,24
python tools\ItemObserver\compare_stack_captures.py
# immediately recapture current addresses, then repeat move/merge as needed
```

Repeat as a separate baseline-created session with different quantities and
preferably another ordinary item type.

## Success criteria

A candidate may advance toward `candidateStackObject` only when it has the
correct transitions, still holds the expected value during immediate context,
has a repeatable bounded layout, survives or explainably relocates through
moves, follows split/merge lifecycle, and shows similar structure in an
independent session. Repeated immediate staleness instead supports a transient
mirror and should trigger a different event-correlated read-only evidence source.
