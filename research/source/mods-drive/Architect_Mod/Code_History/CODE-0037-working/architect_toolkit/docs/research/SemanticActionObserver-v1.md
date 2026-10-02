# Architect Semantic Action Observer v1

## Scope and safety

This is a read-only extension of the proven Architect native runtime for
Enshrouded 0.9.1.2 / revision 1076226 / Hotfix #42. It preserves the existing
build validation, injector, F7 dashboard, F8 builder, bridge, logging, and
stable `BuildingPlaceEvent` detour. It adds no inventory, input, world, save,
voxel, player, or admin mutation.

Hook threads enqueue fixed-size records only. The existing worker thread drains
the bounded 64-event ring and performs file I/O. Identical building events
within 10 ms are deduplicated. Ring overrun is counted. Shutdown stops semantic
publication before the existing detour restoration and DLL unload path.

## Build profile and static evidence

`SemanticActionBuildProfile.h` records the supported executable SHA-256 and the
already-proven building placement evidence. Runtime compatibility remains
authoritative through the existing exact unique function signature plus
allocator-sequence validation.

The current executable contains the following strings in `.rdata`:

| Research target | String RVAs |
| --- | --- |
| `InventoryTransferAction` | `0x13FBDA0`, `0x1C35134`, `0x1C351D3`, `0x1C3A09F`, `0x1C5A378` |
| `createBuildingItemAction` | `0x13FFD40` |
| `buildingStockCycleAction` | `0x13FFE18` |
| `ServerConsumedPlayerInput` | `0x1C52773`, `0x1C547C7`, `0x1C58754`, `0x1C587D8`, `0x1C58867`, `0x1C5C2B8`, `0x1C5C324`, `0x1C5C3E3` |

These are string locations, not execution points. No validated instruction
signature, calling convention, or native transient-object layout connects them
to a safe hook. Accordingly no RVA placeholder or hook is installed for the
three target actions.

## Observer boundaries

`SemanticActionObserver.h/.c` owns the bounded thread-safe publication ring,
deduplication, lifecycle, observer state, and fail-closed target status.
`ArchitectNativeRuntime.c` retains build discovery, the proven hook, worker,
JSON serialization, file publication, and clean uninstall.

The proven placement hook publishes:

- material;
- `trackingItemId`;
- thread and monotonic tick;
- validated hook address and RVA.

The event reports `createBuildingItemActionItemId: null` and `itemIdMatch: null`.
It does not pretend the still-unobserved create-item action has been correlated.

## Diagnostics

`bridge/semantic_actions.jsonl` contains structured records with build,
observer, status, thread, payload, correlation, and address evidence.
`bridge/semantic_action_status.json` contains build support, signature/hook
state, event/drop counts, most recent action, and failure reason. F7 Diagnostics
and `executor_status.json` surface this summary without enabling actions.

Runtime status classifications:

| Mapping | Status | Evidence |
| --- | --- | --- |
| Existing `BuildingPlaceEvent` observation | **PROVEN** | Existing unique signature, expected allocation sequence, live capture history |
| Semantic JSONL publication from that hook | **EXPERIMENTAL** | Built and offline-validated; requires a live placement test |
| `keen::ItemStack` reflected `id/count/pide` schema | **PROVEN** | Reflected schema only; not asserted as every transient native object layout |
| Inventory transfer native execution point | **UNSOLVED** | Strings/schema exist; no validated executable consumer or calling convention |
| Create-building-item native execution point | **UNSOLVED** | Reflected action exists; no safe hook or consumed-version mapping |
| Building stock-cycle native execution point | **UNSOLVED** | Reflected action exists; no safe hook or consumed-version mapping |
| `createBuildingItemAction.itemId == BuildingPlaceEvent.trackingItemId` | **UNSOLVED** | Create-item side has not been observed live |
| Candidate action field layouts at a future execution point | **INFERRED** | Reflected layouts guide validation but do not prove a native heap layout |

## Build

From the project root in a VS 2019 x64 tools environment:

```powershell
cmd.exe /d /s /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul && cl /nologo /c /O2 /GS- /Zl /W4 /TC /Fo"runtime\native\source\ArchitectNativeRuntime.obj" runtime\native\source\ArchitectNativeRuntime.c && link /nologo /dll /machine:x64 /nodefaultlib /entry:DllMain /out:"runtime\native\ArchitectNativeRuntime.dll" runtime\native\source\ArchitectNativeRuntime.obj runtime\native\source\ArchitectBuildingPlaceEntry.obj runtime\native\source\kernel32.lib vcruntime.lib'
```

Verify the DLL SHA-256 matches `runtime/native/SHA256.txt` before injection.

## Deployment

Deploy these runtime artifacts together:

- `runtime/native/ArchitectNativeRuntime.dll`
- `runtime/native/SHA256.txt`
- `runtime/ArchitectInjector.ps1`

Fully restart Enshrouded before loading v0.14.0; an already-loaded older DLL
cannot be replaced safely in-process.

## Short live test

1. Start Enshrouded and load a disposable test world.
2. Start `runtime/Run Architect Runtime.bat`; confirm v0.14.0 and build ID
   `architect-v014-semantic-observer-20260914-a`.
3. Perform `37 → 13/24 → move 13 → move 24 → merge 37`. Transfer remains
   expected `UNSOLVED`; this confirms no false inventory records appear.
4. Select one known vanilla building piece, preview it, and place it once.
5. Select one terrain material, one ordinary block, and one roof material.
   Material-cycle remains expected `UNSOLVED`.
6. Stop through the existing native stop workflow and confirm clean unload.

Return these files:

- `bridge/semantic_actions.jsonl`
- `bridge/semantic_action_status.json`
- `bridge/building_capture.json`
- `bridge/native_status.json`
- `bridge/native_runtime.log`
- `bridge/upstream_trace.json`

## First unresolved mapping

The first priority blocker is the executable consumer/dispatch point for
`InventoryTransferAction`. The next evidence step is bounded offline xref and
data-flow analysis from its reflected metadata to a uniquely validated semantic
execution point. No hook should be proposed until its argument provenance and
expected instructions are established.
