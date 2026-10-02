# Building KFC ingestion — revision 1076226

The supplied bundle is verified before use:

* bundle SHA-256: `153BE9AF6875DB39594FDCAC7A08EE8B316C802BE8A426D24F0A9DFAE713C474`
* executable SHA-256: `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`

`tools/ArchitectDataIndex/builder.py` extracts the nested archives under
`data/kfc_sources/building_1076226/` and records the bundle plus each nested
archive hash in `input_sources`. The original zip is never modified.

## Ingested coverage

The current rebuild contains 3,616 ItemInfo identities (including the
previously audited Architect records), 3,527 resolved ItemRegistry links,
1,955 recipes, 5,724 recipe inputs, 1,943 recipe outputs, 141 blueprint
records, 112 terrain configurations, 86 building configurations, 258
material-layer records, 249 MaterialFeedback resources, and 31 normalized snap rules across seven
VoxelBlueprintConfig families. Unresolved references are retained in
`unresolved_refs` rather than discarded.

Building/terrain classification uses `equipment.voxelData` fields from the
ItemInfo source. The `placeVoxelMaterialId >= 128` building split is recorded
as source-backed evidence; configuration joins are only attached when the
material ID is present in the corresponding registry.

Snap rules preserve the source fields verbatim (including the source spelling
`lenghtwiseAdjacent`/`lenghtwiseEnclosing`) inside normalized rule `fields`.
No missing fields or relationships are invented.

## Validation

`bridge/build_catalog_validation.json` reports resolved relationship counts,
unresolved IDs (94 currently, retained rather than dropped), duplicate
identities, source files, compression checks, and bundle provenance.
The F8 catalog remains read-only and displays the real snap families/rules;
selecting a catalog row still creates no game command.

Families without supplied records remain explicitly unavailable: templates,
attributes, perks, skill nodes, impacts, actor sequences, map markers, and
camera states. Recipe inputs/outputs and all supplied building-focused families
are now populated from the bundle.
