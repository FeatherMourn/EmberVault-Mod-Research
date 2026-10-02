# Architect Semantic Action Observer v0.16.0

## Results

`BuildingPlaceEvent` remains **PROVEN**. Live v0.15 evidence showed three
committed placements produced three pairs, while preview/cancel produced no
event. The pair members matched in grid, orientation, volume, material,
tracking item, and caller but deliberately differed in context and thread.

v0.16 therefore excludes context and thread from pair equality. It buffers one
raw placement record for at most 50 ms so both matching records receive the same
`candidateLogicalPlacementId`, `candidatePair: true`, common `pairDeltaMs`, and
local diagnostic `candidateSideIndex` values 0 and 1. Both raw records remain in
the log. No semantic side name is assigned.

Every runtime creates a `sessionId`, deletes the prior active
`semantic_actions.jsonl` before hooks are enabled, and includes the ID in status
and every new semantic record. This prevents cross-session correlation.

## Current inventory-move site

Historical external evidence reported an old-build inventory move pointer at
RVA `0x340D13` with prefix `4C 8B 7C 24 28 48 8B 55`. That RVA is not used.

Against revision 1076226 / executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`,
the prefix occurs exactly once at current RVA `0x388453`. The expanded exact
current sequence also occurs once:

```text
4C 8B 7C 24 28 48 8B 55 08 49 8B CF
E8 2C B4 93 00 84 C0 0F 84 95 00 00 00
```

The enclosing `.pdata` function is `0x3883C0..0x388552`. Relevant flow:

```text
0x388421 lea  rcx,[rsp+20]
0x388426 mov  rdx,rbp
0x388429 call 0x387830
0x38842E cmp  byte ptr [rsp+20],0
0x388433 je   0x388453
0x388453 mov  r15,qword ptr [rsp+28]
0x388458 mov  rdx,qword ptr [rbp+08]
0x38845C mov  rcx,r15
0x38845F call 0xCC3890
0x388464 test al,al
```

No direct rel32 caller of the enclosing function was decoded; dispatch may be
indirect. The stack result is nevertheless structurally strong: helper
`0x387830` receives the address of the result region at `[rsp+0x20]`, its status
byte is tested, and adjacent qword `[rsp+0x28]` becomes R15. Downstream code
reads/writes dword fields at R15 offsets `+0x00`, `+0x04`, and `+0x08`, matching
the reflected 0x0C `keen::ItemStack` shape. This supports a probe but does not
yet prove the runtime semantic interpretation.

Machine-readable bounded disassembly is in
`bridge/inventory_move_pointer_site_scan.json`.

## Build

From a VS 2019 x64 tools environment, assemble the probe shim, compile the
freestanding runtime, and link both shims:

```powershell
ml64 /nologo /c /Fo"runtime\native\source\ArchitectInventoryMoveProbeEntry.obj" "runtime\native\source\ArchitectInventoryMoveProbeEntry.asm"
cl /nologo /c /O2 /GS- /Zl /W4 /TC /Fo"runtime\native\source\ArchitectNativeRuntime.obj" "runtime\native\source\ArchitectNativeRuntime.c"
link /nologo /dll /machine:x64 /nodefaultlib /entry:DllMain /out:"runtime\native\ArchitectNativeRuntime.dll" "runtime\native\source\ArchitectNativeRuntime.obj" "runtime\native\source\ArchitectBuildingPlaceEntry.obj" "runtime\native\source\ArchitectInventoryMoveProbeEntry.obj" "runtime\native\source\kernel32.lib" vcruntime.lib
```

## InventoryMovePointerProbe

The probe is enabled only when all of these hold:

- the existing BuildingPlace build fingerprint validates;
- PE timestamp is `0x6A4236C8` and image size is `0x02DA7000`;
- the 25-byte expanded current sequence has exactly one executable occurrence;
- that occurrence is exactly RVA `0x388453`;
- the 12 complete overwritten instruction bytes match exactly.

The shim replays those three instructions, preserves volatile integer state and
flags around the recorder, and resumes at the untouched direct call at
`0x38845F`. The hook thread performs no file I/O and calls no game function. It
uses existing guarded reads to copy only candidate dwords `+0/+4/+8` plus the
requested bounded register/stack context into a 256-record ring. The worker
writes records named `inventory_move_pointer_probe`.

Evidence classifications remain deliberately separate:

| Claim | Status |
| --- | --- |
| Historical Cheat Table behavior | **EXTERNAL EVIDENCE** |
| Unique current sequence and function structure | **PROVEN STATIC EVIDENCE** |
| Candidate R15 is a live inventory-move ItemStack pointer | **EXPERIMENTAL** |
| InventoryTransferAction consumer | **UNSOLVED** |

No ItemStack value is changed, no inventory action is submitted, no unknown
game function is called, and the old RVA is never installed.

## Exact live test

1. Fully stop any older Architect runtime, then start v0.16.0 in a disposable
   world. Confirm status has a new `sessionId`, `building_place` is `PROVEN`,
   `inventory_move_pointer_probe.runtime.hookInstalled` is true, and
   `inventory_transfer` remains `UNSOLVED`.
2. Do not perform unrelated inventory operations. Use one known stack whose
   visible count is exactly 37.
3. Split it into 13 and 24.
4. Move the 13 stack once.
5. Move the 24 stack once.
6. Merge them back to 37.
7. Perform one ordinary committed Construction Hammer placement. A preview and
   cancel may be performed first as a negative control.
8. Stop through the normal Architect native stop workflow and wait for clean
   unload before copying evidence.

Return exactly:

- `bridge/semantic_actions.jsonl`
- `bridge/semantic_action_status.json`
- `bridge/native_runtime.log`
- `bridge/native_status.json`
- `bridge/building_capture.json`
- `bridge/upstream_trace.json`

Also retain `bridge/inventory_move_pointer_site_scan.json` as the static report;
it does not need to be regenerated after the live test.
