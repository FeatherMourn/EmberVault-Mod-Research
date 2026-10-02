# Ring → Filled Circle carrier mutation safety design

Design only. No write implementation is present in this batch.

## Scope

The future experiment would temporarily replace only the Ring placement-cache
record payload bytes with the existing Filled Circle bytes. It would not alter
ItemInfo, ItemRegistry entries, resolver keys, table metadata, selection state,
dimensions, or preview resources.

## Required pre-write gates

1. Supported executable fingerprint and validated record/cache layout.
2. Ring record (`1458989991`) and Filled Circle record (`3094089500`) both
   resolve in the same functionally validated cache.
3. Both records report the expected dimensions and exactly eight payload bytes.
4. Compression flags are equal and payload pointers are non-null.
5. Both source and destination payload ranges pass page-boundary-aware guarded
   reads; the destination range additionally passes writable-page checks.
6. The Ring bytes equal the previously captured expected Ring signature
   `3c7ec3c3c3c37e3c`; the source bytes equal the expected Filled Circle
   signature `3c7effffffff7e3c`.
7. No array resize, capacity change, resource recreation, or allocator call is
   allowed. Any unknown capacity semantics fail closed.

## Transaction sequence

* Revalidate every pointer, length, dimension, compression flag, and expected
  source bytes immediately before the operation.
* Copy the eight original Ring bytes into private diagnostic backup storage.
* Perform one exact bounded byte copy from the already-existing Filled Circle
  payload into the already-existing Ring payload storage.
* Immediately guarded-read all eight destination bytes and require an exact
  match with the Filled Circle signature. A mismatch triggers restoration and
  records failure.
* Forward the ordinary placement path unchanged.
* Immediately restore the eight saved Ring bytes, guarded and exact-length.
* Verify the restored bytes equal the backup. Restoration failure is a hard
  failure and must disarm the experiment.

## Failure conditions

Fail closed without writing for any signature mismatch, missing record,
different dimensions or compression, zero/oversized length, unreadable source,
non-writable destination, pointer arithmetic overflow, changing cache metadata,
failed backup, failed post-write verification, exception, timeout, or uncertain
array capacity. Never attempt a partial copy or fallback target.

## Unload behavior

The experiment must be disarmed before unload. If a write is in flight, guarded
cleanup restores the saved bytes before returning. Unload must restore any hook
bytes and release only diagnostic-owned allocations; it must not free or resize
game resource storage. If restoration cannot be proven successful, the build
must fail closed and surface the condition rather than continuing.
