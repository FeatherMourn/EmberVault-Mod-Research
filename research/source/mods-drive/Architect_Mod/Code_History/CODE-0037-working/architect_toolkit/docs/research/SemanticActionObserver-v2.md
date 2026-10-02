# Semantic Action Observer v0.15 research

## Outcome

The current-build `BuildingPlaceEvent` mapping remains **PROVEN** independently
of whether its hook is currently installed. Runtime status now reports
`signatureFound`, `hookInstalled`, `hookEverInstalled`, `eventCount`,
`droppedEventCount`, `stoppedCleanly`, and `lastFailureReason` separately.

The v0.14 10 ms broad duplicate suppression was removed. Each hook invocation is
published as a raw JSONL event with sequence/timing/thread data, context, grid,
orientation and volume bit patterns, material and tracking item, hook RVA/address,
and caller/return evidence. Conservative adjacent-event correlation labels only
`candidateLogicalPlacementId`, `candidatePair`, and its reason when the complete
payload and transform match within 50 ms. `sideClassification` is always null;
the observer makes no client/server or preview/commit claim.

## InventoryTransferAction focused static analysis

Reflected size is `0x20`: VersionedData `+0x00`, source entity `+0x04`, target
entity `+0x08`, source SlotId `+0x0C` (8 bytes), target SlotId `+0x14` (8 bytes),
type `+0x1C`, flags `+0x1D`, and uint16 amount `+0x1E`.

The offline current-build scanner found 14 target-string occurrences but no
decoded direct executable xrefs. It found 138 register-local multi-offset
clusters, none with sufficient identity and argument provenance for a safe hook.
The historical prefix occurs exactly once at RVA `0x388453`; this is recorded as
a location clue only and was not reused as a signature.

Two superficially interesting clusters were manually rejected:

- `0x8FA60..0x8FB30` accesses `+0x0C/+0x10/+0x14/+0x18/+0x1C/+0x1D/+0x1E`,
  but also `+0x20/+0x30/+0x31/+0x36/+0x58/+0x98`; its `+0x1E` access is a byte,
  not the schema's uint16 amount. Direct callers at `0x8A5F5` and `0x8F96F` do
  not establish action identity.
- `0xC9609..0xC96FE` forms several field addresses but has no established action
  argument provenance or ItemStack consumer evidence and is consistent with a
  generic reflection/serialization traversal.

Consequently InventoryTransferAction is **UNSOLVED**, hook readiness is
`NOT_READY`, and its runtime hook remains disabled fail-closed. Reproducible
machine-readable evidence is in `bridge/inventory_transfer_consumer_scan.json`;
the scanner is `tools/ItemObserver/scan_inventory_transfer_consumer.py`.

## Safety boundary

No inventory hook, game call, registry write, item mutation, side classification,
or historical-AOB installation is introduced. The only active semantic source is
the already validated, uniquely matched BuildingPlaceEvent hook.
