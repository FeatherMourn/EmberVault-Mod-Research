# Architect Semantic Action Observer v0.21.0

## Scope and safety

This milestone is an offline/static research pass for Enshrouded revision
1076226 (executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`). It
preserves the proven `BuildingPlaceEvent` observer and the inventory control
subsystem. No action, selection, placement, registry, world, or save memory is
written. No new native detour is installed.

## Reflected action evidence

`keen::ecs::CreateBuildingItemAction` is **PROVEN_STATIC_BUILD_1076226**:

| field | offset | width |
| --- | ---: | ---: |
| `versionData` | `+0x00` | 4 |
| `selectedIndex` | `+0x04` | 4 |
| `itemId` | `+0x08` | 4 |

The reflected type is `0x0C` bytes with four-byte alignment. The reflected
`ClientPlayerInput.createBuildingItemAction`,
`ServerConsumedPlayerInput.consumedCreateBuildingItemAction`, and
client-only `UiCreateBuildingItemEvent` references remain research breadcrumbs;
they do not independently establish a native object address or calling
convention.

## Offline static result

`tools/SemanticActionObserver/scan_create_building_item_static.py` analyzes the
on-disk executable using its `.pdata` function boundaries and decoded x64
instructions. It records string RVAs, data-table pointer references, direct RIP
xrefs, and bounded complete-field shape candidates in
`bridge/create_building_item_static_map.json`.

The scan found metadata/data-table references for the action names and many
generic functions that read offsets `+0x00`, `+0x04`, and `+0x08` from one base
register. Those matches are not action consumers: the same pattern is common
for unrelated three-field records, serialization helpers, and dispatch data.
No candidate has all of the evidence required for a hook:

1. a uniquely identified action pointer and calling convention;
2. a complete-field data-flow chain from the reflected action;
3. a consumed-version read/update tied to that action; and
4. a validated downstream edge toward the proven placement path.

Consequently the native consumer status is **UNSOLVED** and the observer
decision is **disabled/fail-closed**. The existing BuildingPlaceEvent hook is
unchanged. No RVA placeholder is installed, and no `UiBuildingEvent`, resolver,
selector, or action hook is re-enabled.

`UiCreateBuildingItemEvent` has the same status: its strings and metadata are
present, but no independently validated native path establishes whether it
dispatches into `CreateBuildingItemAction`, mirrors it, or belongs to another
UI-only route. It remains **UNSOLVED** and is not hooked.

This is an explicit negative result, not evidence that the action is absent at
runtime. A future safe site must be established from an action-specific
dispatch/data-flow edge rather than from a field-offset coincidence.

## Analyzer support

`tools/SemanticCaptureAnalyzer/analyzer.py` now accepts future
`observer=create_building_item_action` JSONL records. It normalizes
`versionRaw`, `selectedIndexRaw`, and `itemIdRaw`, resolves IDs only through
the offline `ArchitectDataIndex`, and reports the nearest committed placement
without asserting causality. Correlations are explicitly
`INSUFFICIENT_EVIDENCE` until a live consumer and lifecycle are proven.

The analyzer distinguishes:

- selection vs preview vs cancel vs commit: **UNSOLVED** until a capture tags
  the lifecycle;
- action `itemId` equal to placement `trackingItemId`: a reported equality is
  only a capture observation, not a causal claim;
- consumed-version behavior: **UNSOLVED** until a validated owner/field path
  exists.

## Controlled live test prepared (not performed here)

After a future build proves a safe observer, use a disposable world:

1. Select `Blueprint_Voxel_Block_Foundation_4m`; leave preview visible, then
   cancel.
2. Select `Blueprint_Terrain_Whitebox_2x2_Cube`; leave preview visible, then
   cancel.
3. Select the foundation again and commit exactly one placement.
4. Select the terrain cube and commit exactly one placement.

The expected evidence is whether action records occur at selection, preview,
cancel, and commit, whether `selectedIndex` repeats, whether the consumed
version advances, and whether an observed action ID equals the later placement
ID. No live test is requested for this static-only milestone.

## Files

- `bridge/create_building_item_static_map.json` — generated static evidence;
- `tools/SemanticActionObserver/scan_create_building_item_static.py` — bounded
  offline scanner;
- `tools/SemanticCaptureAnalyzer/analyzer.py` — future-record normalization and
  conservative correlation;
- `docs/research/SemanticActionObserver-v8.md` — this status ledger.
