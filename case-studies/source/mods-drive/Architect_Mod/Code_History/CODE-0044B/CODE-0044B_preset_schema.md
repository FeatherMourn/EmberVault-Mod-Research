# CODE-0044B procedural preset schema

Storage: `data/build_presets/procedural_shapes.json` within the installed Architect toolkit.
The library schema is `architect.procedural_presets.v1`; each record's shape spec and
record schema are `architect.procedural_shape.v1`.

Library fields: `schema`, `presets`, with unrelated top-level metadata preserved.
Record fields: `id`, `schema`, `name`, `spec`, `family`, `parameters`, `dimensions`,
`voxelCount`, `occupancyHash`, optional `matchingCatalogKey`, `createdUtc`, `modifiedUtc`.
The normalized `spec` contains `schema`, `family`, and parameters `width`, `height`,
`depth`, `radius`, `hollow`, `thickness`, `axis`.

On load, schema and parameter types/ranges are checked; geometry is regenerated;
stored family, parameters, dimensions, voxel count, and occupancy hash must match.
The catalog match is recalculated from the authoritative catalog before enabling
restart staging; a stored `matchingCatalogKey` is never trusted to activate a shape.
Equal occupancy hashes are labeled `DUPLICATE DESIGN` in the preset UI.

Writes serialize and validate a same-directory temporary file, then use atomic
file replacement for existing libraries (or same-directory move for first save).
A simulated failure before replacement preserves the previous library. No native
pointer, game process state, or generated Blueprint resource is stored.
