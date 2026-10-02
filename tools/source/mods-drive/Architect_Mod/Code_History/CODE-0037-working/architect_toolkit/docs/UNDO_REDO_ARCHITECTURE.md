# Offline undo/redo transaction architecture

This is an implementation-independent format proposal. It has no Enshrouded
runtime integration and performs no file or game-state mutation.

## Transaction envelope

Each operation is a journal record with a UUID, monotonic sequence, UTC time,
operation kind (`placement`, `fill`, `replace`, `paint`, `terrain_edit`, or
`multi_chunk_structure`), grouped-operation ID, and schema version. A record
contains the affected chunk coordinates and a deterministic before/after voxel
diff. A diff stores sorted local voxel indices, old value, and new value; runs
of equal values may be compressed with a bounded byte-run encoding.

```json
{
  "schemaVersion": 1,
  "transactionId": "uuid",
  "groupId": "uuid-or-null",
  "kind": "placement",
  "chunks": [{
    "coordinate": [0, 0, 0],
    "before": {"encoding": "rle-u8", "bytes": "..."},
    "after": {"encoding": "rle-u8", "bytes": "..."}
  }],
  "memoryBudgetBytes": 1048576,
  "checksum": "sha256"
}
```

The journal writer must reserve a bounded memory budget before accepting a
transaction. If the diff would exceed the budget, the operation is rejected or
split into explicitly grouped records; it is never partially committed.

## Undo/redo semantics

Undo applies each chunk's `before` image in reverse chunk order. Redo applies
`after` images in forward order. Any new operation after an undo invalidates
the redo stack from that point (branching history is not implicit). Grouped
operations undo and redo atomically at the group boundary, while retaining
per-chunk checksums for recovery.

## Crash-safe journal

Use an append-only journal with length, schema, transaction ID, payload, and
checksum. Flush the record, then append a commit marker containing the same
checksum. Recovery replays only records with a valid commit marker; an
incomplete tail is ignored/truncated. Periodic snapshots may compact committed
history, but the snapshot is written to a sibling temporary file, flushed,
atomically replaced, and followed by a journal checkpoint.

`placement`, `fill`, `replace`, `paint`, and `terrain_edit` all use the same
voxel-diff envelope. `multi_chunk_structure` is simply a grouped collection of
chunk diffs with a single commit boundary. No operation assumes a particular
game allocator, object layout, or native API.
