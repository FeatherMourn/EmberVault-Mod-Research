# Item Observer Call-Graph Research v2

## Proven

The offline scanner uses Capstone 5.0.7 for instruction decoding and PE-file
`.pdata` entries for x64 function boundaries. It analysed only the executable
with SHA-256 `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
No process was opened.

* `backpackSplitStack` is at RVA `0x1C4F360`. It has no direct decoded code
  reference. Two `.rdata` qword values resolve to it (`0x1663D60` and
  `0x19CF130`), but neither data object has a decoded code reference.
* `consumedInventoryTransferAction` is at RVA `0x1C5A370`. It has no direct
  decoded code reference. Two `.rdata` qword values resolve to it
  (`0x19ECB30` and `0x1A13580`); neither is referenced directly from code.
  A third relative-offset occurrence at `0x1C5A36C` is retained as raw data
  evidence only, not treated as a table or handler.
* The stack-deletion message is loaded by `lea rdx, [rip + 0x107c128]` at
  RVA `0x389161`. Its containing `.pdata` function is
  `0x389136..0x389222`. That function calls `0x7DB950` and `0xCB4B50` but
  has no direct `rel32` caller. This confirms a logging/error-context path;
  it is not an inventory-operation hook candidate.

## Inferred

The qword objects around the two action strings have nearby values resolving
back into `.rdata`, which is consistent with metadata/registration-like data.
It does not establish an entry stride, handler pointer, dispatch role, or
function relationship.

## Candidates

There are no ranked code-function candidates. The data objects above remain
`CANDIDATE` data relationships only.

## Disproven

* A direct RIP-relative string xref is not available for either target action.
* RVA `0x389161` is not approved as an observer hook target.

## No-hook decision

**NOT READY.** No candidate has a target-specific code relationship, a
validated inventory calling context, or an argument-capture strategy.

## Run

```powershell
python tools\ItemObserver\scan_item_observer_callgraph.py
```

This writes `bridge/item_observer_callgraph_scan.json`. The script uses a
bounded, target-focused reference search; candidate byte patterns are decoded
by Capstone before being reported.

## Next research step

Inspect the `.rdata` metadata objects that contain the split-stack and
transfer-action names, following their containing structures/neighbor entries
with a format-aware disassembler. The next useful question is whether the
metadata is reached through a hash/name dispatcher rather than direct code
references.
