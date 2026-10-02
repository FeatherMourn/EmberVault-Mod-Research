# Semantic Building Catalog v1

## Purpose and safety

The v0.24 catalog turns locally verified ArchitectDataIndex records into a
searchable, player-facing read-only view. Selecting a row creates no command,
does not alter the Construction Hammer, and never writes game memory. The F8
placement controls remain unchanged.

## Data model

`tools/ArchitectDataIndex/build_catalog.py` reads the build-locked SQLite index
for Enshrouded revision `1076226` and emits `bridge/build_catalog.json`. The
index is populated from the verified building KFC bundle as well as the
project's prior audited exports. It preserves ItemId, GUID, resource type/hash,
part/content identity, category, equipment slot, registry membership, source
blueprint identity, dimensions, recipe inputs/outputs, material configuration,
and evidence status. IDs are accepted only from explicit source fields; no
debug-name or GUID hashing is performed.

Classification prefers structural evidence in this order:

* a verified blueprint registry mapping → `Voxel Blueprint`;
* `placeVoxelMaterialId >= 128` → `Building Block Material`;
* `placeVoxelMaterialId < 128` → `Terrain Material`;
* explicit `BlueprintMaterial_Roof`/`BlueprintMaterial_*` slots;
* `BuildTool`/category metadata as weaker evidence.

Unavailable fields remain `null` or `unavailable`; they are never represented
as zero. Current local coverage is partial: the index contains verified item,
item-registry, recipe-output, and blueprint rows, while terrain/building
configuration bodies and snap-rule rows are unavailable.

## Vanilla snap catalog

`bridge/snap_rule_catalog.json` is generated from the normalized
`blueprint_snap_rules` table. The verified bundle currently contributes seven
configuration families and 31 rules. Rule fields are preserved from source,
including target/exclusion GUIDs, distance limits, adjacency/enclosing flags,
and directional behavior. Missing fields remain absent rather than being
invented.

## F8 usage

1. Run the offline index/catalog generation (or the regression script).
2. Start the existing Architect runtime shell and press F8.
3. Select the `Build Catalog` tab.
4. Search by name, ItemId, GUID, material ID, or snap family and optionally
   filter Blueprints, Terrain, Blocks, Roofs, or Tools.
5. Select a row to inspect identity, registry, building/material, blueprint,
   crafting, snapping, and evidence fields.

Catalog selection is informational only. `backendStatus` is
`read_only_catalog`; `ArchitectBuildSelection` is not submitted to
Enshrouded. Last-placement diagnostics continue to come only from the proven
BuildingPlaceEvent observer and are not attributed to catalog selection.

## Limitations and future work

The current local exports still do not establish every non-building resource
family or a native semantic selection setter. Those families remain explicitly
unavailable/partial. Future semantic-action work must establish an independent
safe game-side mapping before enabling any action; this feature does not do so.
