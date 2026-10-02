# Structure coordinates — Enshrouded build 1076226

The BuildingPlaceEvent `grid` vector is retained as three signed integer
Q32.32 components (`scale = 4294967296 = 2^32`). Raw values are evidence and
are never converted through a floating-point intermediate. World coordinates
are derived as `raw / scale`; local coordinates are derived as
`(raw - originRaw) / scale`, so subtraction remains exact even for large
world positions.

## Bounds

Each placement volume is translated by its local placement position before
the aggregate envelope is calculated. Identity quaternions use exact corner
translation. Non-identity rotations use a bounded eight-corner quaternion
transform and are explicitly marked inferred until an independent game
transform convention is established.

## Migration and provenance

v0.29 files containing integral JSON floats are accepted only when the value
is finite, integral, and exactly representable (at most 2^53). Non-integral
or precision-losing coordinates fail validation. Recorder output preserves
`raw.position`, `raw.positionRaw`, and `raw.gridRaw` as integer arrays.

Recorder provenance distinguishes semantic stream rows from building rows:
`semanticStreamEventsObserved`, `buildingRawEventsInRecordingWindow`,
`pairedBuildingRawEvents`, `logicalPlacementsRecorded`,
`ambiguousBuildingRawEvents`, and `ignoredNonBuildingEvents`. The recording
window carries source session identity plus start/end raw sequence numbers.

Snap families remain unresolved unless an explicit item-to-snap relationship is
present in the catalog; debug-name matching is not used.
