# Architect Semantic Action Observer v0.19.0

## Outcome

v0.19 adds one build-locked, read-only probe at RVA `0x37182C`, inside the
statically proven `0x371810..0x37229F` InventoryTransferAction consumer. The
site is after the function stack probe and where `RSI=[RDX+0x10]` becomes
available. The hook replays exactly 14 overwritten bytes, preserves volatile
integer state and flags, and resumes at `0x37183A`.

Installation requires the revision-1076226 executable fingerprint, PE timestamp
and image size, one unique 20-byte signature at the exact RVA, and the exact
14 overwritten bytes. Failure leaves the observer disabled. The existing
BuildingPlaceEvent hook and all v0.18 inventory pre/post hooks are unchanged.

## Capture

The hook copies exactly 0x20 bytes from `RSI+0x08` using guarded reads and
publishes through a bounded 128-record ring. It captures no arbitrary adjacent
memory and performs no file I/O. The worker writes
`inventory_transfer_action_consumer` JSONL records containing raw payload hex,
version, raw source/target identifiers, both packed slot values and indices,
type, flags, uint16 amount, thread/tick, and consumer address.

The statically established `context+0x38 -> pointee+0x20` chain is read once at
entry as `candidateConsumedVersionBefore`. When the existing downstream probe
correlates on the same thread and amount within 1000 ms, it performs one guarded
read of the same address as `candidateConsumedVersionAfter`. The destination is
not named ServerConsumedPlayerInput and is never written.

## Correlation and confidence

The hook-side neutral operation ID is the action event sequence. Existing move
records carry it only when same-thread, equal-amount, bounded-time evidence
matches. Raw records are never suppressed. The offline SemanticCaptureAnalyzer
adds amount and source/target slot comparisons, downstream arithmetic, type
distribution, consumed-version observations, and ArchitectDataIndex item-name
enrichment.

Starting classifications are:

- action structure: **PROVEN_STATIC_BUILD_1076226**;
- live consumer and source/target slot mappings: **EXPERIMENTAL**;
- destination ItemStack and amount: **PROVEN_BUILD_1076226**;
- source ItemStack: **EXPERIMENTAL**;
- version consumption: **INFERRED**;
- inventory ownership and producer/indirect dispatch: **UNSOLVED**;
- ClientPlayerInput and ServerConsumedPlayerInput ownership: **UNSOLVED**;
- R14 first dword match: **PROVEN_BUILD_1076226**;
- R14 concrete type: **INFERRED**, not concrete ItemInfo*.

## Exact live test

Use a disposable world and one terrain-stone stack containing 37 items:

1. Start v0.19 and confirm all three inventory probe entries report installed,
   a fresh `v019-` session, and zero drops.
2. Split 37 into 13 and 24.
3. Move the 13 stack once, then the 24 stack once.
4. Merge them back to 37.
5. Preview and cancel one building placement, then commit one placement.
6. Stop through the normal native stop workflow and wait for clean unload.
7. Run `python tools/SemanticCaptureAnalyzer/analyze.py`.

Return exactly:

- `bridge/semantic_actions.jsonl`
- `bridge/semantic_action_status.json`
- `bridge/native_runtime.log`
- `bridge/native_status.json`
- `bridge/building_capture.json`
- `bridge/upstream_trace.json`
- `bridge/analysis/latest_semantic_capture_report.json`
- `bridge/analysis/latest_semantic_capture_report.md`

No action, version, identifier, slot, ItemStack, registry, selector, or world
state is written by this observer.
